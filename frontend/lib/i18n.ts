export type Lang = "en" | "vi";

export const STRINGS = {
  en: {
    title: "Lumi Home support",
    subtitle: "AI assistant · replies instantly",
    greeting: "Hi! I can check your order, answer questions about shipping and returns, or open a ticket for our team. How can I help?",
    placeholder: "Type your message…",
    send: "Send",
    ticket: "Ticket created",
    error: "Something went wrong. Please try again.",
    tools: {
      search_help_articles: "Searching the help center…",
      get_order: "Looking up your order…",
      cancel_order: "Cancelling the order…",
      create_ticket: "Creating a ticket…",
    },
    suggestions: ["Where is my order?", "What is your return policy?", "My item arrived damaged"],
  },
  vi: {
    title: "Hỗ trợ Lumi Home",
    subtitle: "Trợ lý AI · trả lời ngay",
    greeting: "Xin chào! Mình có thể kiểm tra đơn hàng, giải đáp về giao hàng và đổi trả, hoặc tạo yêu cầu hỗ trợ cho đội ngũ. Bạn cần giúp gì ạ?",
    placeholder: "Nhập tin nhắn…",
    send: "Gửi",
    ticket: "Đã tạo yêu cầu hỗ trợ",
    error: "Đã có lỗi xảy ra. Vui lòng thử lại.",
    tools: {
      search_help_articles: "Đang tìm trong trung tâm trợ giúp…",
      get_order: "Đang kiểm tra đơn hàng…",
      cancel_order: "Đang hủy đơn hàng…",
      create_ticket: "Đang tạo yêu cầu hỗ trợ…",
    },
    suggestions: ["Đơn hàng của tôi đang ở đâu?", "Chính sách đổi trả thế nào?", "Hàng nhận được bị hỏng"],
  },
} as const;

export function toolLabel(lang: Lang, name: string): string {
  const tools = STRINGS[lang].tools as Record<string, string>;
  return tools[name] ?? "…";
}
