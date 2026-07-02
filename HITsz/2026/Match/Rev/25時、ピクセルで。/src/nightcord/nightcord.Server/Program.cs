using System.Net;
using System.Buffers.Binary;
using System.Net.Sockets;
using System.Security.Cryptography;
using System.Text;
using nightcord.Server.Crypto;
class Program
{
  private const int Port = 8086;
  private const string Magic = "NC01";
  private static readonly byte[] HkdfInfo = Encoding.UTF8.GetBytes("NC-CTF-SESSION");
  private static readonly byte[] HkdfInfoHmac = Encoding.UTF8.GetBytes("NC-CTF-SESSION-HMAC");
  private static ECDsa? ServerSignKey;

  static async Task Main(string[] args)
  {
    ServerSignKey = KeyStore.LoadOrCreateServerKey();
    var listener = new TcpListener(IPAddress.Any, Port);
    listener.Start();
    Console.WriteLine("nightcord.Server listening on 0.0.0.0:{0}", Port);
    while (true)
    {
      var client = await listener.AcceptTcpClientAsync();
      _ = Task.Run(() => HandleClientAsync(client));
    }
  }

  private static async Task HandleClientAsync(TcpClient client)
  {
    using var c = client;
    using var stream = c.GetStream();
    using var br = new BinaryReader(stream, Encoding.UTF8, leaveOpen: true);
    using var bw = new BinaryWriter(stream, Encoding.UTF8, leaveOpen: true);

    try
    {
      // CLIENT_HELLO
      string magic = Encoding.ASCII.GetString(br.ReadBytes(4));
      if (magic != Magic) throw new InvalidDataException("Bad magic");
      int clientPubLen = br.ReadInt32();
      byte[] clientPub = br.ReadBytes(clientPubLen);
      byte[] clientNonce = br.ReadBytes(16);
      byte[] clientSessionId = br.ReadBytes(8);

      using var ecdh = ECDiffieHellman.Create(ECCurve.NamedCurves.nistP256);
      byte[] serverPub = ecdh.PublicKey.ExportSubjectPublicKeyInfo();
      byte[] serverNonce = RandomBytes(16);

      // Server authentication
      byte[] transcript = Concat(Encoding.ASCII.GetBytes(Magic), clientPub, clientNonce, clientSessionId, serverPub, serverNonce);
      if (ServerSignKey == null) throw new InvalidOperationException("Signing key not initialized");
      byte[] serverSig = ServerSignKey.SignData(transcript, HashAlgorithmName.SHA256);

      // Send SERVER_HELLO
      bw.Write(Encoding.ASCII.GetBytes(Magic));
      bw.Write(serverPub.Length);
      bw.Write(serverPub);
      bw.Write(serverNonce);
      bw.Write(serverSig.Length);
      bw.Write(serverSig);
      await stream.FlushAsync();

      // Derive session keys
      using var clientKey = ECDiffieHellman.Create();
      clientKey.ImportSubjectPublicKeyInfo(clientPub, out _);
      byte[] shared = ecdh.DeriveKeyFromHash(clientKey.PublicKey, HashAlgorithmName.SHA256);
      // Use HKDF with nonces as salt
      byte[] sessionKey = Hkdf.DeriveKey(shared, Concat(clientNonce, serverNonce), HkdfInfo, 32);
      byte[] sessionNonceBase = Hkdf.DeriveKey(shared, Concat(serverNonce, clientNonce), HkdfInfo, 12);
      byte[] hmacKey = Hkdf.DeriveKey(shared, Concat(serverNonce, clientNonce), HkdfInfoHmac, 32);

      // CLIENT_FINISH
      int finMacLen = br.ReadInt32();
      byte[] finMac = br.ReadBytes(finMacLen);
      byte[] expectedFin;
      using (var hmac = new HMACSHA256(hmacKey))
        expectedFin = hmac.ComputeHash(Encoding.ASCII.GetBytes("client-finish"));
      if (!FixedTimeEquals(finMac, expectedFin)) throw new InvalidDataException("Bad finish MAC");

      // Receive app message
      byte type = br.ReadByte();
      if (type != 0x30) throw new InvalidDataException("Unexpected client message");
      int seq = br.ReadInt32();
      int clen = br.ReadInt32();
      byte[] ctext = br.ReadBytes(clen);
      int macLen = br.ReadInt32();
      byte[] mac = br.ReadBytes(macLen);
      byte[] header = new byte[1 + 4];
      header[0] = type;
      BinaryPrimitives.WriteUInt32LittleEndian(header.AsSpan(1, 4), (uint)seq);
      byte[] macInput = Concat(header, ctext);
      using (var hmac = new HMACSHA256(hmacKey))
      {
        var expected = hmac.ComputeHash(macInput);
        if (!FixedTimeEquals(expected, mac)) throw new InvalidDataException("Bad MAC");
      }
      // Decrypt
      byte[] nonce = XorNonce(sessionNonceBase, (uint)seq);
      var chacha = new NCChaCha20(sessionKey, nonce);
      byte[] plain = new byte[ctext.Length];
      chacha.ProcessBytes(ctext, plain);
      string text = Encoding.UTF8.GetString(plain);
      if (text != "I got it!")
        throw new InvalidDataException("Invalid app payload");
      // Send encrypted flag
      string flag = ReadFlag();
      string reply = "FLAG: " + flag;
      byte[] p = Encoding.UTF8.GetBytes(reply);
      int sseq = 2;
      var snonce = XorNonce(sessionNonceBase, (uint)sseq);
      var ch2 = new NCChaCha20(sessionKey, snonce);
      byte[] ciph = new byte[p.Length];
      ch2.ProcessBytes(p, ciph);
      // HMAC
      header = new byte[1 + 4];
      header[0] = 0x31;
      BinaryPrimitives.WriteUInt32LittleEndian(header.AsSpan(1, 4), (uint)sseq);
      macInput = Concat(header, ciph);
      using var hmac2 = new HMACSHA256(hmacKey);
      var smac = hmac2.ComputeHash(macInput);
      bw.Write(header[0]);
      bw.Write(sseq);
      bw.Write(ciph.Length);
      bw.Write(ciph);
      bw.Write(smac.Length);
      bw.Write(smac);
      await stream.FlushAsync();
    }
    catch (Exception ex)
    {
      Console.WriteLine("[!] Connection error: " + ex.Message);
    }
  }

  private static string ReadFlag()
  {
    try
    {
      var path = Path.Combine(AppContext.BaseDirectory, "flag.txt");
      if (File.Exists(path))
      {
        return File.ReadAllText(path).Trim();
      }
    }
    catch { }
    return "flag{placeholder}";
  }

  private static byte[] XorNonce(byte[] baseNonce, uint seq)
  {
    byte[] res = (byte[])baseNonce.Clone();
    Span<byte> s = stackalloc byte[4];
    BinaryPrimitives.WriteUInt32LittleEndian(s, seq);
    for (int i = 0; i < 4; i++) res[i] ^= s[i];
    return res;
  }

  private static byte[] Concat(params byte[][] arrays)
  {
    int len = 0; foreach (var a in arrays) len += a.Length;
    var r = new byte[len];
    int pos = 0;
    foreach (var a in arrays) { Buffer.BlockCopy(a, 0, r, pos, a.Length); pos += a.Length; }
    return r;
  }

  private static bool FixedTimeEquals(ReadOnlySpan<byte> a, ReadOnlySpan<byte> b)
  {
    if (a.Length != b.Length) return false;
    int diff = 0;
    for (int i = 0; i < a.Length; i++) diff |= a[i] ^ b[i];
    return diff == 0;
  }

  private static byte[] RandomBytes(int n)
  {
    var b = new byte[n];
    RandomNumberGenerator.Fill(b);
    return b;
  }
}
