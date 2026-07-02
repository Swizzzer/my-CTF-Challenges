using System;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;

namespace nightcord.Core
{
  /// <summary>
  /// Controls playback of an Animation.
  /// </summary>
  internal struct AnimationPlayer
  {
    public Animation? Animation => animation;
    private Animation? animation;

    public int FrameIndex => frameIndex;
    private int frameIndex;

    private float time;

    public Vector2 Origin
    {
      get
      {
        if (Animation == null) return Vector2.Zero;
        return new Vector2(Animation.FrameWidth / 2.0f, Animation.FrameHeight);
      }
    }

    public void PlayAnimation(Animation animation)
    {
      if (Animation == animation)
        return;
      this.animation = animation;
      frameIndex = 0;
      time = 0f;
    }

    public void Draw(GameTime gameTime, SpriteBatch spriteBatch, Vector2 position, SpriteEffects spriteEffects)
    {
      Draw(gameTime, spriteBatch, position, spriteEffects, Color.White);
    }

    public void Draw(GameTime gameTime, SpriteBatch spriteBatch, Vector2 position, SpriteEffects spriteEffects, Color color)
    {
      if (Animation == null)
        throw new NotSupportedException("No animation set for AnimationPlayer.");

      time += (float)gameTime.ElapsedGameTime.TotalSeconds;
      while (time > Animation.FrameTime)
      {
        time -= Animation.FrameTime;
        if (Animation.IsLooping)
          frameIndex = (frameIndex + 1) % Animation.FrameCount;
        else
          frameIndex = Math.Min(frameIndex + 1, Animation.FrameCount - 1);
      }

      Rectangle source = new Rectangle(
          frameIndex * Animation.Texture.Height,
          0,
          Animation.Texture.Height,
          Animation.Texture.Height);

      spriteBatch.Draw(Animation.Texture, position, source, color, 0f, Origin, 1f, spriteEffects, 0f);
    }
  }
}

