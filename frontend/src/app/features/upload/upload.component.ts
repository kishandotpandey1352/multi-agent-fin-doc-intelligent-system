import { Component, EventEmitter, Input, Output } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

export interface UploadPayload {
  file: File;
  company: string;
  sourceType: string;
}

@Component({
  selector: 'app-upload',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './upload.component.html',
  styleUrl: './upload.component.css'
})
export class UploadComponent {
  @Input() status = '';
  @Input() loading = false;
  @Output() upload = new EventEmitter<UploadPayload>();

  uploadCompany = 'tesla';
  uploadSourceType = 'annual';
  uploadFile: File | null = null;

  onFileSelected(event: Event): void {
    const target = event.target as HTMLInputElement;
    this.uploadFile = target.files && target.files.length ? target.files[0] : null;
  }

  submitUpload(): void {
    if (!this.uploadFile) {
      this.status = 'Please choose a PDF file.';
      return;
    }
    this.upload.emit({
      file: this.uploadFile,
      company: this.uploadCompany,
      sourceType: this.uploadSourceType
    });
  }
}
