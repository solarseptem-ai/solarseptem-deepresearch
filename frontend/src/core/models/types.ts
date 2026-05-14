export interface Model {
  id: string;
  name: string;
  model: string;
  display_name: string;
  description?: string | null;
  supports_thinking?: boolean;
  supports_reasoning_effort?: boolean;
}

export interface ProviderModel {
  id: string;
  name: string;
  supports_multimodal: boolean | null;
  supports_image: boolean | null;
  supports_video: boolean | null;
  probe_source: string | null;
  is_free: boolean;
  generate_kwargs: Record<string, unknown>;
}

export interface Provider {
  id: string;
  name: string;
  base_url: string;
  api_key: string;
  chat_model: string;
  models: ProviderModel[];
  extra_models: ProviderModel[];
  api_key_prefix: string;
  is_local: boolean;
  freeze_url: boolean;
  require_api_key: boolean;
  is_custom: boolean;
  support_model_discovery: boolean;
  support_connection_check: boolean;
  generate_kwargs: Record<string, unknown>;
  meta: Record<string, unknown>;
}
