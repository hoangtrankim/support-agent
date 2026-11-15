import ChatWidget from "@/components/ChatWidget";

export default async function WidgetPage({ searchParams }: { searchParams: Promise<{ lang?: string }> }) {
  const { lang } = await searchParams;
  return <ChatWidget lang={lang === "vi" ? "vi" : "en"} />;
}
