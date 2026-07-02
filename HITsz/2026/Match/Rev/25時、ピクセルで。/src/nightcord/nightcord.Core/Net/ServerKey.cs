using System;
using System.IO;
using System.Security.Cryptography;

namespace nightcord.Core.Net
{
  internal static class ServerKey
  {
    private const string DefaultPemFilename = "server-ecdsa-public.pem";

    public static ECDsa LoadServerPublicKey()
    {
      var ecdsa = ECDsa.Create();

      string baseDir = AppContext.BaseDirectory;
      string path = Path.Combine(baseDir, DefaultPemFilename);

      if (File.Exists(path))
      {
        string pem = File.ReadAllText(path);
        ecdsa.ImportFromPem(pem);
        return ecdsa;
      }


      ecdsa.Dispose();
      throw new FileNotFoundException("Pinned server public key PEM not found. Place server-ecdsa-public.pem next to the game executable.");
    }
  }
}

