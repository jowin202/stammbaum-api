import { Routes } from '@angular/router';
import { PersonSteckbriefComponent } from './components/steckbrief/steckbrief';


export const routes: Routes = [
  // ... andere Routen
  { path: 'personen/:id', component: PersonSteckbriefComponent },
];