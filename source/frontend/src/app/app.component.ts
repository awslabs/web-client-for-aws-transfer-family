import { Component, NgZone } from '@angular/core';
import { trigger, state, style, transition, animate } from '@angular/animations';

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html'
})
export class AppComponent {

  sidebarActive: boolean;

  onMenuButtonClick(event: Event) {
    this.sidebarActive = !this.sidebarActive;

    event.preventDefault();
  }
}
