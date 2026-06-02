import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { DomSanitizer, SafeHtml } from '@angular/platform-browser';
import { AnswerResponse } from '../../services/api.service';

@Component({
  selector: 'app-output',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './output.component.html',
  styleUrl: './output.component.css'
})
export class OutputComponent {
  @Input() response: AnswerResponse | null = null;

  constructor(private readonly sanitizer: DomSanitizer) {}

  trustSvg(svg: unknown): SafeHtml {
    if (typeof svg !== 'string') {
      return '';
    }
    return this.sanitizer.bypassSecurityTrustHtml(svg);
  }
}
