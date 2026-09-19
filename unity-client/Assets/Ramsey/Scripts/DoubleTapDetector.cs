namespace Ramsey
{
    public sealed class DoubleTapDetector
    {
        float first = -10, last = -10, quietUntil;
        bool high;
        public void Reset(float now) { first = last = -10; high = false; quietUntil = now + .4f; }
        public bool Sample(float peak, float threshold, float now)
        {
            bool onset = peak >= threshold && !high;
            high = peak >= threshold * .45f;
            if (!onset || now < quietUntil || now - last < .09f) return false;
            last = now;
            float gap = now - first;
            if (gap >= .12f && gap <= .65f) { Reset(now); quietUntil = now + 1.2f; return true; }
            first = now; return false;
        }
    }
}
