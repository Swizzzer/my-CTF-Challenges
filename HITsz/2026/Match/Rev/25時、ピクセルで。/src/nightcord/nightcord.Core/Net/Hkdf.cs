using System;
using System.Security.Cryptography;

namespace nightcord.Core.Net
{
  internal static class Hkdf
  {
    public static byte[] DeriveKey(byte[] ikm, byte[] salt, byte[] info, int length)
    {
      if (length <= 0) throw new ArgumentOutOfRangeException(nameof(length));
      using var hmac = new HMACSHA256(salt ?? Array.Empty<byte>());
      byte[] prk = hmac.ComputeHash(ikm);

      byte[] okm = new byte[length];
      byte[] previous = Array.Empty<byte>();
      int generated = 0;
      int counter = 1;
      while (generated < length)
      {
        hmac.Key = prk;
        byte[] input = new byte[previous.Length + (info?.Length ?? 0) + 1];
        Buffer.BlockCopy(previous, 0, input, 0, previous.Length);
        if (info != null && info.Length > 0)
          Buffer.BlockCopy(info, 0, input, previous.Length, info.Length);
        input[input.Length - 1] = (byte)counter;
        previous = hmac.ComputeHash(input);

        int toCopy = Math.Min(previous.Length, length - generated);
        Buffer.BlockCopy(previous, 0, okm, generated, toCopy);
        generated += toCopy;
        counter++;
      }

      Array.Clear(prk, 0, prk.Length);
      Array.Clear(previous, 0, previous.Length);
      return okm;
    }
  }
}

