import { Component, EventEmitter, Input, OnInit, Output } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

export interface IndexPayload {
  company_filters?: string[];
  max_docs?: number | null;
  max_pages?: number | null;
  reset_index?: boolean;
}

@Component({
  selector: 'app-indexing',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './indexing.component.html',
  styleUrl: './indexing.component.css'
})
export class IndexingComponent implements OnInit {
  @Input() status = '';
  @Input() initialCompanyFilters = 'tesla,apple,nvidia';
  @Input() initialMaxDocs: number | null = 6;
  @Input() initialMaxPages: number | null = 8;
  @Input() initialReset = true;
  @Output() start = new EventEmitter<IndexPayload>();

  companyFilters = '';
  maxDocs: number | null = null;
  maxPages: number | null = null;
  resetIndex = true;

  ngOnInit(): void {
    this.companyFilters = this.initialCompanyFilters;
    this.maxDocs = this.initialMaxDocs;
    this.maxPages = this.initialMaxPages;
    this.resetIndex = this.initialReset;
  }

  startIndex(): void {
    const filters = this.companyFilters
      .split(',')
      .map((value) => value.trim())
      .filter(Boolean);
    this.start.emit({
      company_filters: filters.length ? filters : undefined,
      max_docs: this.maxDocs,
      max_pages: this.maxPages,
      reset_index: this.resetIndex
    });
  }
}
