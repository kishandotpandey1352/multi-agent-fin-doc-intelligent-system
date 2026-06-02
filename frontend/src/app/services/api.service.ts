import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface AnswerResponse {
  answer: string;
  executive_summary: string;
  findings: string[];
  risks: string[];
  citations: Array<Record<string, unknown>>;
  citations_formatted: string[];
  confidence_score: number;
  confidence_note: string;
  evidence_count: number;
  plan?: Record<string, unknown>;
  retrieval?: Record<string, unknown>;
  critic?: Record<string, unknown>;
}

export interface QueryPayload {
  question: string;
  company?: string;
  year?: number | null;
  source?: string;
  intent?: string;
  top_k?: number | null;
  final_k?: number | null;
}

@Injectable({
  providedIn: 'root'
})
export class ApiService {
  private readonly baseUrl = 'http://localhost:8000';

  constructor(private readonly http: HttpClient) {}

  uploadPdf(file: File, company: string, sourceType: string): Observable<{ staged_path: string }> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('company', company);
    formData.append('source_type', sourceType);
    return this.http.post<{ staged_path: string }>(`${this.baseUrl}/upload`, formData);
  }

  startIndex(payload: {
    company_filters?: string[];
    max_docs?: number | null;
    max_pages?: number | null;
    reset_index?: boolean;
  }): Observable<{ documents: number; chunks: number; vectors: number }> {
    return this.http.post<{ documents: number; chunks: number; vectors: number }>(`${this.baseUrl}/index/start`, payload);
  }

  qa(payload: QueryPayload): Observable<AnswerResponse> {
    return this.http.post<AnswerResponse>(`${this.baseUrl}/qa`, payload);
  }

  summary(payload: QueryPayload): Observable<AnswerResponse> {
    return this.http.post<AnswerResponse>(`${this.baseUrl}/summary`, payload);
  }

  chart(payload: QueryPayload): Observable<AnswerResponse> {
    return this.http.post<AnswerResponse>(`${this.baseUrl}/charts`, payload);
  }

  compare(payload: QueryPayload): Observable<AnswerResponse> {
    return this.http.post<AnswerResponse>(`${this.baseUrl}/compare`, payload);
  }
}
