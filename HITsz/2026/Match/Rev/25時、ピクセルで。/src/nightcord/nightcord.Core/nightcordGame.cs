using System;
using System.Globalization;
using nightcord.Core.Net;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using Microsoft.Xna.Framework.Input;

namespace nightcord.Core
{
  public class nightcordGame : Game
  {
    private GraphicsDeviceManager graphics;
    private SpriteBatch spriteBatch = null!;

    // Content
    private Texture2D bgTexture = null!;
    private Texture2D tileA = null!;
    private Texture2D tileB = null!;
    private Texture2D exitTex = null!;
    private Texture2D toxicIcon = null!;
    private SpriteFont hudFont = null!;
    // Player animation
    private Animation idleAnimation = null!;
    private Animation runAnimation = null!;
    private Animation celebrateAnimation = null!;
    private Animation dieAnimation = null!;
    private AnimationPlayer sprite;
    private SpriteEffects flip = SpriteEffects.None;

    private int tileWidth, tileHeight;
    private int tilesCount;
    private int hazardIndex;
    private Rectangle exitRect;
    private int pathY;

    // Player
    private Rectangle playerRect;
    private float playerSpeed = 180f; // px/s

    // State
    private enum GameState { EnterAddress, Playing, Won, GettingFlag, FlagReceived }
    private GameState state = GameState.EnterAddress;
    private string inputText = "";
    private string serverHost = "127.0.0.1";
    private int serverPort = 8086;

    private int hp = 1;
    private bool itemAvailable = true;
    private bool hazardDamaged = false; // BlockB1 damages once

    private KeyboardState prevKeyboard;

    // Result
    private string? flagString = null;
    private string statusMessage = "";

    public nightcordGame()
    {
      graphics = new GraphicsDeviceManager(this);
      Content.RootDirectory = "Content";
      IsMouseVisible = true;
      IsFixedTimeStep = true;
      TargetElapsedTime = TimeSpan.FromSeconds(1.0 / 60.0);
      graphics.SupportedOrientations = DisplayOrientation.LandscapeLeft | DisplayOrientation.LandscapeRight;
      graphics.PreferredBackBufferWidth = 1280;
      graphics.PreferredBackBufferHeight = 720;
    }

    protected override void Initialize()
    {
      base.Initialize();
    }

    protected override void LoadContent()
    {
      spriteBatch = new SpriteBatch(GraphicsDevice);
      bgTexture = Content.Load<Texture2D>("Backgrounds/Background");
      tileA = Content.Load<Texture2D>("Tiles/BlockA1");
      tileB = Content.Load<Texture2D>("Tiles/BlockB1");
      exitTex = Content.Load<Texture2D>("Tiles/Exit");
      toxicIcon = Content.Load<Texture2D>("Sprites/toxic");
      hudFont = Content.Load<SpriteFont>("Fonts/Hud");
      idleAnimation = new Animation(Content.Load<Texture2D>("Sprites/Player/Idle"), 0.6f, true);
      runAnimation = new Animation(Content.Load<Texture2D>("Sprites/Player/Run"), 0.1f, true);
      celebrateAnimation = new Animation(Content.Load<Texture2D>("Sprites/Player/Celebrate"), 0.1f, false);
      dieAnimation = new Animation(Content.Load<Texture2D>("Sprites/Player/Die"), 0.1f, false);
      sprite.PlayAnimation(idleAnimation);

      tileWidth = tileA.Width;
      tileHeight = tileA.Height;
      SetupLevelLayout();
      ResetLevel();
      // Recompute layout when window size changes
      Window.ClientSizeChanged += (_, __) => RecalculateLayoutOnResize();
    }

    private void SetupLevelLayout()
    {
      var vp = GraphicsDevice.Viewport;
      tilesCount = Math.Max(6, (int)Math.Floor(vp.Width / (float)tileWidth));
      hazardIndex = tilesCount / 2;
      pathY = vp.Height - tileHeight - 40;
      int exitX = (tilesCount - 1) * tileWidth + (vp.Width - tilesCount * tileWidth) / 2;
      int embed = tileHeight / 2;
      exitRect = new Rectangle(exitX, pathY - exitTex.Height + embed, exitTex.Width, exitTex.Height);
    }

    private void RecalculateLayoutOnResize()
    {
      if (tileA == null || exitTex == null) return;

      // Reset the game if currently playing to prevent cheating by resizing window,
      if (state == GameState.Playing)
      {
        SetupLevelLayout();
        ResetLevel();
        return;
      }

      SetupLevelLayout();
      var vp = GraphicsDevice.Viewport;
      int pathLeftX = (vp.Width - tilesCount * tileWidth) / 2;
      int pathRightX = pathLeftX + tilesCount * tileWidth - playerRect.Width;
      if (playerRect.X < pathLeftX) playerRect.X = pathLeftX;
      if (playerRect.X > pathRightX) playerRect.X = pathRightX;
      playerRect.Y = pathY - playerRect.Height;
    }

    private void ResetLevel()
    {
      var vp = GraphicsDevice.Viewport;
      int pathLeftX = (vp.Width - tilesCount * tileWidth) / 2;
      int pw = Math.Max(24, tileWidth / 2);
      int ph = Math.Max(28, tileHeight);
      playerRect = new Rectangle(pathLeftX + 4, pathY - ph, pw, ph);
      hp = 1;
      itemAvailable = true;
      hazardDamaged = false;
      flagString = null;
      statusMessage = "";
      if (state != GameState.EnterAddress)
        state = GameState.Playing;
    }

    protected override void Update(GameTime gameTime)
    {
      if (state == GameState.Playing && hp == 0)
      {
        // Death triggers restart
        ResetLevel();
      }

      var kb = Keyboard.GetState();
      switch (state)
      {
        case GameState.EnterAddress:
          UpdateEnterAddress(kb);
          break;
        case GameState.Playing:
          UpdatePlaying(kb, (float)gameTime.ElapsedGameTime.TotalSeconds);
          break;
        case GameState.Won:
          BeginFetchFlag();
          state = GameState.GettingFlag;
          break;
        case GameState.GettingFlag:
          break;
        case GameState.FlagReceived:
          if (kb.IsKeyDown(Keys.Escape) && !prevKeyboard.IsKeyDown(Keys.Escape))
          {
            ResetLevel();
          }
          break;
      }
      prevKeyboard = kb;
      base.Update(gameTime);
    }

    private void UpdateEnterAddress(KeyboardState kb)
    {
      foreach (var key in Enum.GetValues<Keys>())
      {
        if (kb.IsKeyDown(key) && !prevKeyboard.IsKeyDown(key))
        {
          if (key == Keys.Back && inputText.Length > 0)
          {
            inputText = inputText.Substring(0, inputText.Length - 1);
          }
          else if (key == Keys.Enter)
          {
            if (TryParseAddress(inputText, out serverHost, out serverPort))
            {
              state = GameState.Playing;
            }
            else
            {
              // Default if invalid
              serverHost = "127.0.0.1";
              serverPort = 8086;
              state = GameState.Playing;
            }
          }
          else
          {
            char? ch = KeyToChar(key, kb);
            if (ch.HasValue)
              inputText += ch.Value;
          }
        }
      }
    }

    private static char? KeyToChar(Keys key, KeyboardState kb)
    {
      bool shift = kb.IsKeyDown(Keys.LeftShift) || kb.IsKeyDown(Keys.RightShift);
      return key switch
      {
        >= Keys.D0 and <= Keys.D9 => (char)('0' + (key - Keys.D0)),
        >= Keys.NumPad0 and <= Keys.NumPad9 => (char)('0' + (key - Keys.NumPad0)),
        Keys.OemPeriod => '.',
        Keys.OemMinus => shift ? '_' : '-',
        Keys.OemSemicolon => ':',
        Keys.Space => ' ',
        >= Keys.A and <= Keys.Z => shift ? (char)('A' + (key - Keys.A)) : (char)('a' + (key - Keys.A)),
        _ => null
      };
    }

    private static bool TryParseAddress(string input, out string host, out int port)
    {
      host = "127.0.0.1";
      port = 8086;
      if (string.IsNullOrWhiteSpace(input)) return false;
      var parts = input.Trim().Split(':', StringSplitOptions.RemoveEmptyEntries);
      if (parts.Length != 2) return false;
      host = parts[0];
      if (!int.TryParse(parts[1], NumberStyles.None, CultureInfo.InvariantCulture, out port))
        return false;
      return port > 0 && port < 65536;
    }

    private void UpdatePlaying(KeyboardState kb, float dt)
    {
      float move = 0f;
      if (kb.IsKeyDown(Keys.Left) || kb.IsKeyDown(Keys.A)) move -= 1f;
      if (kb.IsKeyDown(Keys.Right) || kb.IsKeyDown(Keys.D)) move += 1f;
      int dx = (int)Math.Round(move * playerSpeed * dt);
      playerRect.X += dx;
      if (move > 0) flip = SpriteEffects.FlipHorizontally;
      else if (move < 0) flip = SpriteEffects.None;
      if (Math.Abs(move) > 0.01f)
        sprite.PlayAnimation(runAnimation);
      else
        sprite.PlayAnimation(idleAnimation);

      var vp = GraphicsDevice.Viewport;
      int pathLeftX = (vp.Width - tilesCount * tileWidth) / 2;
      int pathRightX = pathLeftX + tilesCount * tileWidth - playerRect.Width;
      if (playerRect.X < pathLeftX) playerRect.X = pathLeftX;
      if (playerRect.X > pathRightX) playerRect.X = pathRightX;

      if (kb.IsKeyDown(Keys.Space) && !prevKeyboard.IsKeyDown(Keys.Space))
      {
        if (itemAvailable)
        {
          hp -= 1;
          itemAvailable = false;
        }
      }

      // Hazard: step onto BlockB1 (center tile) => damage once
      int playerCenterX = playerRect.X + playerRect.Width / 2;
      int centerTileLeft = pathLeftX + hazardIndex * tileWidth;
      var hazardRect = new Rectangle(centerTileLeft, pathY, tileWidth, tileHeight);
      var playerFootRect = new Rectangle(playerRect.X, playerRect.Y + playerRect.Height - 4, playerRect.Width, 8);
      if (!hazardDamaged && playerFootRect.Intersects(hazardRect))
      {
        hp -= 1;
        hazardDamaged = true;
      }

      if (playerRect.Intersects(exitRect))
      {
        sprite.PlayAnimation(celebrateAnimation);
        state = GameState.Won;
      }
    }

    private async void BeginFetchFlag()
    {
      statusMessage = "Contacting server...";
      try
      {
        var client = new CTFClient();
        string flag = await client.GetFlagAsync(serverHost, serverPort);
        flagString = flag;
        statusMessage = "Flag received!";
        state = GameState.FlagReceived;
      }
      catch (Exception ex)
      {
        flagString = "Error: " + ex.Message;
        statusMessage = "Failed to get flag.";
        state = GameState.FlagReceived;
      }
    }

    protected override void Draw(GameTime gameTime)
    {
      GraphicsDevice.Clear(Color.Black);
      spriteBatch.Begin();

      var vp = GraphicsDevice.Viewport;
      spriteBatch.Draw(bgTexture, new Rectangle(0, 0, vp.Width, vp.Height), Color.White);

      if (state == GameState.EnterAddress)
      {
        DrawCentered("Enter server address (IP:PORT)", new Vector2(vp.Width / 2f, vp.Height / 2f - 40), Color.Yellow);
        DrawCentered(inputText + "|", new Vector2(vp.Width / 2f, vp.Height / 2f + 10), Color.White);
        spriteBatch.End();
        base.Draw(gameTime);
        return;
      }

      // Draw path tiles
      int pathLeftX = (vp.Width - tilesCount * tileWidth) / 2;
      for (int i = 0; i < tilesCount; i++)
      {
        var t = (i == hazardIndex) ? tileB : tileA;
        spriteBatch.Draw(t, new Rectangle(pathLeftX + i * tileWidth, pathY, tileWidth, tileHeight), Color.White);
      }

      // Draw exit
      spriteBatch.Draw(exitTex, exitRect, Color.White);

      var playerBottomCenter = new Vector2(playerRect.X + playerRect.Width / 2f, playerRect.Y + playerRect.Height);
      sprite.Draw(gameTime, spriteBatch, playerBottomCenter, flip);

      // HUD
      spriteBatch.DrawString(hudFont, $"HP: {hp}", new Vector2(20, 20), Color.White);
      spriteBatch.Draw(toxicIcon, new Rectangle(20, 60, 40, 40), Color.White);
      spriteBatch.DrawString(hudFont, $"x{(itemAvailable ? 1 : 0)}", new Vector2(70, 65), Color.Yellow);
      spriteBatch.DrawString(hudFont, $"Server: {serverHost}:{serverPort}", new Vector2(20, 110), Color.LightGreen);

      if (state == GameState.GettingFlag || state == GameState.FlagReceived)
      {
        DrawCentered(statusMessage, new Vector2(vp.Width / 2f, vp.Height / 2f - 40), Color.Yellow);
        if (!string.IsNullOrEmpty(flagString))
        {
          DrawCentered(flagString, new Vector2(vp.Width / 2f, vp.Height / 2f + 10), Color.White);
          DrawCentered("Press Esc to replay", new Vector2(vp.Width / 2f, vp.Height / 2f + 50), Color.WhiteSmoke);
        }
      }

      spriteBatch.End();
      base.Draw(gameTime);
    }

    private void DrawCentered(string text, Vector2 center, Color color)
    {
      var size = hudFont.MeasureString(text);
      var pos = center - size / 2f;
      spriteBatch.DrawString(hudFont, text, pos, color);
    }
  }
}
