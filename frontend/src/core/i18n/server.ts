import { cookies } from "next/headers";

import { DEFAULT_LOCALE, normalizeLocale, type Locale } from "./locale";
import { translations } from "./translations";

/** 服务端检测当前用户使用的语言 */
export async function detectLocaleServer(): Promise<Locale> {
  const cookieStore = await cookies();
  let locale = cookieStore.get("locale")?.value;
  if (locale !== undefined) {
    try {
      locale = decodeURIComponent(locale);
    } catch {
      // Keep raw cookie value when decoding fails.
    }
  }

  return normalizeLocale(locale);
}

/** 设置/切换语言，并保存到 Cookie 1年  */
export async function setLocale(locale: string | Locale): Promise<Locale> {
  const normalizedLocale = normalizeLocale(locale);
  const cookieStore = await cookies();
  cookieStore.set("locale", encodeURIComponent(normalizedLocale), {
    maxAge: 365 * 24 * 60 * 60,
    path: "/",
    sameSite: "lax",
  });

  return normalizedLocale;
}

/** 获取当前语言+对应翻译文本  */
export async function getI18n(localeOverride?: string | Locale) {
  const locale = localeOverride
      ? normalizeLocale(localeOverride)
      : await detectLocaleServer();
  const t = translations[locale] ?? translations[DEFAULT_LOCALE];
  return {
    locale,
    t,
  };
}
