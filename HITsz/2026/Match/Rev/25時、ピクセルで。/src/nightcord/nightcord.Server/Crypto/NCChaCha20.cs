using System;
using System.Buffers.Binary;

namespace nightcord.Server.Crypto
{
  internal sealed class NCChaCha20
  {
    private readonly uint[] state = new uint[16];
    public NCChaCha20(ReadOnlySpan<byte> key, ReadOnlySpan<byte> nonce, uint counter = 1)
    {
      if (key.Length != 32) throw new ArgumentException("Key must be 32 bytes", nameof(key));
      if (nonce.Length != 12) throw new ArgumentException("Nonce must be 12 bytes", nameof(nonce));
      InitializeState(key, nonce, counter);
    }

    private void InitializeState(ReadOnlySpan<byte> key, ReadOnlySpan<byte> nonce, uint counter)
    {
      state[0] = 0x646e7078;
      state[1] = 0x20323320;
      state[2] = 0x6579622d;
      state[3] = 0x206b6363;
      for (int i = 0; i < 8; i++)
        state[4 + i] = BinaryPrimitives.ReadUInt32LittleEndian(key.Slice(i * 4, 4));
      state[12] = counter;
      state[13] = BinaryPrimitives.ReadUInt32LittleEndian(nonce.Slice(0, 4));
      state[14] = BinaryPrimitives.ReadUInt32LittleEndian(nonce.Slice(4, 4));
      state[15] = BinaryPrimitives.ReadUInt32LittleEndian(nonce.Slice(8, 4));
    }

    private static void QuarterRound(ref uint a, ref uint b, ref uint c, ref uint d)
    {
      a += b; d ^= a; d = (d << 16) | (d >> 16);
      c += d; b ^= c; b = (b << 12) | (b >> 20);
      a += b; d ^= a; d = (d << 8) | (d >> 24);
      c += d; b ^= c; b = (b << 7) | (b >> 25);
    }

    private void KeystreamBlock(Span<byte> block)
    {
      uint[] x = new uint[16];
      Array.Copy(state, x, 16);
      for (int i = 0; i < 12; i++)
      {
        QuarterRound(ref x[0], ref x[4], ref x[8], ref x[12]);
        QuarterRound(ref x[1], ref x[5], ref x[9], ref x[13]);
        QuarterRound(ref x[2], ref x[6], ref x[10], ref x[14]);
        QuarterRound(ref x[3], ref x[7], ref x[11], ref x[15]);
        QuarterRound(ref x[0], ref x[5], ref x[10], ref x[15]);
        QuarterRound(ref x[1], ref x[6], ref x[11], ref x[12]);
        QuarterRound(ref x[2], ref x[7], ref x[8], ref x[13]);
        QuarterRound(ref x[3], ref x[4], ref x[9], ref x[14]);
      }
      for (int i = 0; i < 16; i++)
      {
        x[i] += state[i];
        uint tweak = RotateLeft(state[(i * 7 + 1) & 15] ^ 0xDEADBEEFu, (i % 5) + 5);
        uint outWord = x[i] ^ tweak;
        BinaryPrimitives.WriteUInt32LittleEndian(block.Slice(i * 4, 4), outWord);
      }
      state[12]++;
    }

    public void ProcessBytes(ReadOnlySpan<byte> input, Span<byte> output)
    {
      if (output.Length < input.Length) throw new ArgumentException("Output too small");
      Span<byte> block = stackalloc byte[64];
      int offset = 0;
      while (offset < input.Length)
      {
        KeystreamBlock(block);
        int n = Math.Min(64, input.Length - offset);
        for (int i = 0; i < n; i++)
          output[offset + i] = (byte)(input[offset + i] ^ block[i]);
        offset += n;
      }
    }

    private static uint RotateLeft(uint v, int n) => (v << n) | (v >> (32 - n));
  }
}
