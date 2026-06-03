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
  styleUrls: ['./app.css']
})
export class App {
  uploadStatus = '';
  uploadLoading = false;
  indexStatus = '';
  indexOpen = false;

  response: AnswerResponse | null = null;
  responseStatus = '';
  isLoading = false;
  showResponseModal = false;
  modeIndex = 0;
  modes: Array<'deterministic' | 'augment' | 'replace'> = ['deterministic', 'augment', 'replace'];

  constructor(private readonly api: ApiService) {}

  setMode(index: number): void {
    this.modeIndex = index;
  }

  submitUpload(payload: UploadPayload): void {
    this.uploadStatus = 'Uploading...';
    this.uploadLoading = true;
    this.api.uploadPdf(payload.file, payload.company, payload.sourceType)
      .pipe(finalize(() => {
        this.uploadLoading = false;
      }))
      .subscribe({
        next: (data) => {
          const t = data?.upload_time_seconds;
          this.uploadStatus = t ? `Upload successful (${t}s)` : 'Upload successful.';
          // brief UI hint: show small toast-like indicator by opening index panel
          this.indexStatus = 'Ready to index.';
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
        const t = (data as any)?.index_time_seconds;
        this.indexStatus = t
          ? `Indexed ${data.documents} documents, ${data.chunks} chunks. (${t}s)`
          : `Indexed ${data.documents} documents, ${data.chunks} chunks.`;
      },
      error: (err) => {
        this.indexStatus = err?.error?.detail || 'Indexing failed.';
      }
    });
  }

  toggleIndex(): void {
    this.indexOpen = !this.indexOpen;
  }

  openResponse(): void {
    this.showResponseModal = true;
  }

  closeResponse(): void {
    this.showResponseModal = false;
  }

  runQuery(event: { endpoint: QueryEndpoint; payload: QueryPayload }): void {
    this.isLoading = true;
    this.responseStatus = 'Working on it...';
    event.payload.mode = this.modes[this.modeIndex];
    const call =
      event.endpoint === 'qa'
        ? this.api.qa(event.payload)
        : event.endpoint === 'summary'
        ? this.api.summary(event.payload)
        : event.endpoint === 'chart'
        ? this.api.chart(event.payload)
        : this.api.compare(event.payload);

    call.pipe(
      finalize(() => {
        this.isLoading = false;
      })
    ).subscribe({
      next: (data) => {
        // Log response for debugging persistent loading
        // eslint-disable-next-line no-console
        console.debug('runQuery response:', data);
        this.response = data;
        this.responseStatus = 'Done.';
        this.showResponseModal = true;
      },
      error: (err) => {
        // eslint-disable-next-line no-console
        console.error('runQuery error:', err);
        this.response = null;
        this.responseStatus = err?.error?.detail || 'Request failed.';
      }
    });
  }
}
