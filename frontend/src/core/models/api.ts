import { getBackendBaseURL } from "../config";

import type { Model, Provider, ProviderModel } from "./types";

export async function loadModels() {
  const res = await fetch(`${getBackendBaseURL()}/api/models`);
  const { models } = (await res.json()) as { models: Model[] };
  return models;
}

export async function loadProviders() {
  const res = await fetch(`${getBackendBaseURL()}/api/provider`);
  const providers = (await res.json()) as Provider[];
  return providers;
}

export async function fetchProviderModels(providerId: string): Promise<ProviderModel[]> {
  const res = await fetch(`${getBackendBaseURL()}/api/${providerId}/models`, {
    method: "POST",
    headers: {
      accept: "application/json",
    },
  });
  const data = await res.json();
  if (data.success) {
    return data.models as ProviderModel[];
  }
  throw new Error(data.error || "获取模型列表失败");
}
