import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

/** 拼接 + 合并 Tailwind 类名 */
export function cn(...inputs: ClassValue[]) {
    return twMerge(clsx(inputs));
}

/** 外部链接的共享类（默认为下划线）。 */
export const externalLinkClass =
    "text-primary underline underline-offset-2 hover:no-underline";


/** 默认情况下，链接样式不带下划线（例如用于流式传输/加载）。 */
export const externalLinkClassNoUnderline = "text-primary hover:underline";
