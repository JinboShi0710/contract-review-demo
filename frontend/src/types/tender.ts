export type TenderStatus = "created" | "processing" | "completed" | "failed";
export type TenderCategory = "disqualification" | "scoring" | "materials" | "key_parameters" | "timeline" | "contract_terms" | "technical_requirements" | "acceptance_delivery";

export interface TenderReviewItem {
  id: string;
  category: TenderCategory;
  title: string;
  requirement: string;
  evidence_quote: string;
  source_page?: number;
  source_line?: number;
  importance: "required" | "attention" | "reference";
  action?: string;
  source: "keyword" | "llm";
}

export interface TenderTask {
  id: string;
  file_name: string;
  title?: string;
  status: TenderStatus;
  page_count?: number;
  line_count?: number;
  summary?: string;
  error_message?: string;
  created_at: string;
  categories?: Record<TenderCategory, string>;
  items?: TenderReviewItem[];
}

export interface TenderUploadResponse { task_id: string; status: string; file_name: string; }
export interface TenderListResponse { items: TenderTask[]; total: number; }
