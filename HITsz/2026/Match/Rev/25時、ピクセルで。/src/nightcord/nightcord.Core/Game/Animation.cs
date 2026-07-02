using Microsoft.Xna.Framework.Graphics;

namespace nightcord.Core
{
    /// <summary>
    /// Represents an animated texture with square frames laid out horizontally.
    /// </summary>
    internal class Animation
    {
        public Texture2D Texture { get; }
        public float FrameTime { get; }
        public bool IsLooping { get; }

        public int FrameCount => Texture.Width / FrameHeight;
        public int FrameWidth => Texture.Height;
        public int FrameHeight => Texture.Height;

        public Animation(Texture2D texture, float frameTime, bool isLooping)
        {
            Texture = texture;
            FrameTime = frameTime;
            IsLooping = isLooping;
        }
    }
}

