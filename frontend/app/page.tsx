import Script from "next/script";
import DemoPanel from "@/components/DemoPanel";

export default function Page() {
  return (
    <main className="shop">
      <nav>
        <span className="shop-logo">Lumi Home</span>
        <span className="nav-links">Living · Bedroom · Kitchen · Sale</span>
      </nav>
      <section className="hero">
        <h1>Calm, well-made things for your home</h1>
        <p>This is a demo storefront. The real product is the AI support agent in the corner.</p>
      </section>
      <DemoPanel />
      <footer>Demo project · Claude tool use, FastAPI, Next.js</footer>
      <Script src="/embed.js" data-lang="en" strategy="afterInteractive" />
    </main>
  );
}
