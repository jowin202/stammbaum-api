import { Component } from '@angular/core';
import { PersonSteckbriefComponent } from "./components/steckbrief/steckbrief";

@Component({
  selector: 'app-root',
  imports: [PersonSteckbriefComponent],
  templateUrl: './app.html',
  styleUrl: './app.css'
})
export class App {
  protected title = 'frontend';
}
