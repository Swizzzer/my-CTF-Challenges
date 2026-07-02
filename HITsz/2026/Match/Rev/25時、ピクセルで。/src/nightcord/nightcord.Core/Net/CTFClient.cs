using System;
using System.Buffers.Binary;
using System.IO;
using System.Net.Sockets;
using System.Security.Cryptography;
using System.Text;
using System.Threading.Tasks;

namespace nightcord.Core.Net
{
  internal sealed class CTFClient
  {
    private const string Magic = "NC01";
    private static readonly byte[] HkdfInfo = Encoding.UTF8.GetBytes("NC-CTF-SESSION");
    private static readonly byte[] HkdfInfoHmac = Encoding.UTF8.GetBytes("NC-CTF-SESSION-HMAC");

    public async Task<string> GetFlagAsync(string host, int port)
    {
      using var client = new TcpClient();
      await client.ConnectAsync(host, port);
      using var stream = client.GetStream();
      using var br = new BinaryReader(stream, Encoding.UTF8, leaveOpen: true);
      using var bw = new BinaryWriter(stream, Encoding.UTF8, leaveOpen: true);

      // CLIENT_HELLO
      using var ecdh = ECDiffieHellman.Create(ECCurve.NamedCurves.nistP256);
      byte[] clientPub = ecdh.PublicKey.ExportSubjectPublicKeyInfo();
      byte[] clientNonce = RandomBytes(16);
      byte[] clientSessionId = RandomBytes(8);

      WriteString(bw, Magic);
      bw.Write((int)clientPub.Length);
      bw.Write(clientPub);
      bw.Write(clientNonce);
      bw.Write(clientSessionId);
      await stream.FlushAsync();

      // SERVER_HELLO
      string magic = ReadString(br, 4);
      if (magic != Magic) throw new InvalidDataException("Bad magic");
      int serverPubLen = br.ReadInt32();
      byte[] serverPub = br.ReadBytes(serverPubLen);
      byte[] serverNonce = br.ReadBytes(16);
      int sigLen = br.ReadInt32();
      byte[] serverSig = br.ReadBytes(sigLen);

      // Derive shared secret
      using var serverKey = ECDiffieHellman.Create();
      serverKey.ImportSubjectPublicKeyInfo(serverPub, out _);
      byte[] shared = ecdh.DeriveKeyFromHash(serverKey.PublicKey, HashAlgorithmName.SHA256);

      // Verify server ECDSA signature with pinned public key
      byte[] transcript = Concat(Encoding.ASCII.GetBytes(Magic), clientPub, clientNonce, clientSessionId, serverPub, serverNonce);
      using (var ecdsa = ServerKey.LoadServerPublicKey())
      {
        if (!ecdsa.VerifyData(transcript, serverSig, HashAlgorithmName.SHA256))
          throw new InvalidDataException("Server authentication failed");
      }

      // Key schedule
      byte[] sessionKey = Hkdf.DeriveKey(shared, Concat(clientNonce, serverNonce), HkdfInfo, 32);
      byte[] sessionNonceBase = Hkdf.DeriveKey(shared, Concat(serverNonce, clientNonce), HkdfInfo, 12);
      byte[] hmacKey = Hkdf.DeriveKey(shared, Concat(serverNonce, clientNonce), HkdfInfoHmac, 32);

      // CLIENT_FINISH
      byte[] finishMac;
      using (var hmac = new HMACSHA256(hmacKey))
        finishMac = hmac.ComputeHash(Encoding.ASCII.GetBytes("client-finish"));
      bw.Write(finishMac.Length);
      bw.Write(finishMac);
      await stream.FlushAsync();

      // Send encrypted "I got it!"
      string payload = "I got it!";
      byte[] plaintext = Encoding.UTF8.GetBytes(payload);
      // Derive message nonce = sessionNonceBase XOR seq(4 bytes repeated)
      uint seq = 1;
      byte[] msgNonce = XorNonce(sessionNonceBase, seq);
      var chacha = new NCChaCha20(sessionKey, msgNonce);
      byte[] ciphertext = new byte[plaintext.Length];
      chacha.ProcessBytes(plaintext, ciphertext);
      // HMAC over type||seq||ciphertext
      byte[] macInput;
      {
        byte[] header = new byte[1 + 4];
        header[0] = 0x30;
        BinaryPrimitives.WriteUInt32LittleEndian(header.AsSpan(1, 4), seq);
        macInput = Concat(header, ciphertext);
      }
      byte[] mac;
      using (var hmac = new HMACSHA256(hmacKey))
        mac = hmac.ComputeHash(macInput);

      bw.Write((byte)0x30);
      bw.Write((int)seq);
      bw.Write(ciphertext.Length);
      bw.Write(ciphertext);
      bw.Write(mac.Length);
      bw.Write(mac);
      await stream.FlushAsync();

      byte type = br.ReadByte();
      if (type != 0x31) throw new InvalidDataException("Unexpected server message");
      int rseq = br.ReadInt32();
      int clen = br.ReadInt32();
      byte[] ctext = br.ReadBytes(clen);
      int tagLen = br.ReadInt32();
      byte[] rmac = br.ReadBytes(tagLen);
      // Verify MAC
      {
        byte[] header = new byte[1 + 4];
        header[0] = type;
        BinaryPrimitives.WriteUInt32LittleEndian(header.AsSpan(1, 4), (uint)rseq);
        macInput = Concat(header, ctext);
      }
      using (var hmac = new HMACSHA256(hmacKey))
        mac = hmac.ComputeHash(macInput);
      if (!FixedTimeEquals(mac, rmac)) throw new InvalidDataException("Bad MAC");
      byte[] snonce = XorNonce(sessionNonceBase, (uint)rseq);
      var ch2 = new NCChaCha20(sessionKey, snonce);
      byte[] plain = new byte[ctext.Length];
      ch2.ProcessBytes(ctext, plain);
      return Encoding.UTF8.GetString(plain);
    }

    private static byte[] XorNonce(byte[] baseNonce, uint seq)
    {
      byte[] res = (byte[])baseNonce.Clone();
      Span<byte> s = stackalloc byte[4];
      BinaryPrimitives.WriteUInt32LittleEndian(s, seq);
      for (int i = 0; i < 4; i++)
        res[i] ^= s[i];
      return res;
    }

    private static byte[] RandomBytes(int n)
    {
      var b = new byte[n];
      RandomNumberGenerator.Fill(b);
      return b;
    }

    private static byte[] Concat(params byte[][] arrays)
    {
      int len = 0;
      foreach (var a in arrays) len += a.Length;
      var r = new byte[len];
      int pos = 0;
      foreach (var a in arrays)
      {
        Buffer.BlockCopy(a, 0, r, pos, a.Length);
        pos += a.Length;
      }
      return r;
    }

    private static bool FixedTimeEquals(ReadOnlySpan<byte> a, ReadOnlySpan<byte> b)
    {
      if (a.Length != b.Length) return false;
      int diff = 0;
      for (int i = 0; i < a.Length; i++) diff |= a[i] ^ b[i];
      return diff == 0;
    }

    private static void WriteString(BinaryWriter bw, string s)
    {
      var bytes = Encoding.ASCII.GetBytes(s);
      bw.Write(bytes);
    }

    private static string ReadString(BinaryReader br, int length)
    {
      var b = br.ReadBytes(length);
      return Encoding.ASCII.GetString(b);
    }
  }
}
