using System;
using System.IO;
using System.Security.Cryptography;

namespace nightcord.Server.Crypto
{
  internal static class KeyStore
  {
    private const string PrivatePemFile = "server-ecdsa-private.pem";
    private const string PublicPemFile = "server-ecdsa-public.pem";

    public static ECDsa LoadOrCreateServerKey()
    {
      string baseDir = AppContext.BaseDirectory;
      string privPath = Path.Combine(baseDir, PrivatePemFile);
      string pubPath = Path.Combine(baseDir, PublicPemFile);

      if (File.Exists(privPath))
      {
        var ecdsa = ECDsa.Create();
        try
        {
          string pem = File.ReadAllText(privPath);
          ecdsa.ImportFromPem(pem);
        }
        catch
        {
          ecdsa.Dispose();
          throw;
        }
        return ecdsa;
      }
      else
      {
        using var tmp = ECDsa.Create(ECCurve.NamedCurves.nistP256);
        string privPem = tmp.ExportECPrivateKeyPem();
        string pubPem = tmp.ExportSubjectPublicKeyInfoPem();

        File.WriteAllText(privPath, privPem);
        File.WriteAllText(pubPath, pubPem);

        var ecdsa = ECDsa.Create();
        ecdsa.ImportFromPem(privPem);
        return ecdsa;
      }
    }
  }
}

