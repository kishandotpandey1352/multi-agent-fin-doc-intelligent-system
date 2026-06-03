import { Component, EventEmitter, Input, Output } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

export interface QueryPayload {
  question: string;
  company?: string;
  year?: number | null;
  source?: string;
  intent?: string;
  top_k?: number | null;
  final_k?: number | null;
  mode?: string;
}

export type QueryEndpoint = 'qa' | 'summary' | 'chart' | 'compare';

@Component({
  selector: 'app-query',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './query.component.html',
  styleUrls: ['./query.component.css']
})
export class QueryComponent {
  @Input() status = '';
  @Input() loading = false;
  @Input() mode: 'deterministic' | 'augment' | 'replace' = 'deterministic';
  @Output() run = new EventEmitter<{ endpoint: QueryEndpoint; payload: QueryPayload }>();

  question = '';
  questionCompany = '';
  questionYear: number | null = null;
  questionSource = 'auto';
  questionIntent = 'qa';
  topK: number | null = 12;
  finalK: number | null = 8;

  submit(endpoint: QueryEndpoint): void {
    if (!this.question.trim()) {
      this.status = 'Enter a question to continue.';
      return;
    }

    this.run.emit({
      endpoint,
      payload: {
        question: this.question,
        company: this.questionCompany || undefined,
        year: this.questionYear || undefined,
        source: this.questionSource,
        intent: this.questionIntent,
        top_k: this.topK,
        final_k: this.finalK,
        mode: this.mode
      }
    });
  }
}
