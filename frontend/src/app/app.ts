import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ApiService, AnswerResponse } from './services/api.service';
import { finalize } from 'rxjs/operators';
import { UploadComponent, UploadPayload } from './features/upload/upload.component';
import { IndexingComponent, IndexPayload } from './features/indexing/indexing.component';
import { QueryComponent, QueryEndpoint, QueryPayload } from './features/query/query.component';
import { OutputComponent } from './features/output/output.component';
import { MatTabsModule } from '@angular/material/tabs';
import { MatCardModule } from '@angular/material/card';

@Component({
  selector: 'app-root',
  imports: [CommonModule, UploadComponent, IndexingComponent, QueryComponent, OutputComponent, MatTabsModule, MatCardModule],
  templateUrl: './app.html',
  styleUrl: './app.css'
})
export class App {
  uploadStatus = '';
  uploadLoading = false;
  indexStatus = '';

  response: AnswerResponse | null = null;
  responseStatus = '';
  isLoading = false;

  constructor(private readonly api: ApiService) {}

  submitUpload(payload: UploadPayload): void {
    this.uploadStatus = 'Uploading...';
    this.uploadLoading = true;
    this.api.uploadPdf(payload.file, payload.company, payload.sourceType)
      .pipe(finalize(() => {
        this.uploadLoading = false;
      }))
      .subscribe({
        next: () => {
          this.uploadStatus = 'Upload successful.';
        },
        error: (err) => {
          this.uploadStatus = err?.error?.detail || 'Upload failed.';
        }
      });
  }

  startIndex(payload: IndexPayload): void {
    this.indexStatus = 'Indexing...';
    this.api.startIndex(payload).subscribe({
      next: (data) => {
        this.indexStatus = `Indexed ${data.documents} documents, ${data.chunks} chunks.`;
      },
      error: (err) => {
        this.indexStatus = err?.error?.detail || 'Indexing failed.';
      }
    });
  }

  runQuery(event: { endpoint: QueryEndpoint; payload: QueryPayload }): void {
    this.isLoading = true;
    this.responseStatus = 'Working on it...';
    const call =
      event.endpoint === 'qa'
        ? this.api.qa(event.payload)
        : event.endpoint === 'summary'
        ? this.api.summary(event.payload)
        : event.endpoint === 'chart'
        ? this.api.chart(event.payload)
        : this.api.compare(event.payload);

    call.subscribe({
      next: (data) => {
        this.response = data;
        this.responseStatus = 'Done.';
        this.isLoading = false;
      },
      error: (err) => {
        this.response = null;
        this.responseStatus = err?.error?.detail || 'Request failed.';
        this.isLoading = false;
      }
    });
  }
}
