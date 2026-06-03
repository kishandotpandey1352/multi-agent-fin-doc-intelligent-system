import { Component, Input, OnChanges, SimpleChanges } from '@angular/core';
import { CommonModule } from '@angular/common';
import { DomSanitizer, SafeHtml } from '@angular/platform-browser';
import { AnswerResponse } from '../../services/api.service';

@Component({
  selector: 'app-output',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './output.component.html',
  styleUrls: ['./output.component.css']
})
export class OutputComponent {
  @Input() response: AnswerResponse | null = null;

  constructor(private readonly sanitizer: DomSanitizer) {}

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['response'] && this.response) {
      try {
        // Log the response for debugging chart rendering issues
        // eslint-disable-next-line no-console
        console.debug('OutputComponent response:', this.response);
      } catch (e) {
        // ignore
      }
    }
  }

  trustSvg(svg: unknown): SafeHtml {
    if (typeof svg !== 'string') {
      return this.sanitizer.bypassSecurityTrustHtml('');
    }
    return this.sanitizer.bypassSecurityTrustHtml(svg);
  }
}
