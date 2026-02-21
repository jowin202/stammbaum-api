import { Component, signal, inject, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormControl, ReactiveFormsModule } from '@angular/forms';
import { HttpClient } from '@angular/common/http';

// Material Imports
import { MatAutocompleteModule } from '@angular/material/autocomplete';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatCardModule } from '@angular/material/card';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatDialog, MatDialogModule } from '@angular/material/dialog';
import { MatSnackBar } from '@angular/material/snack-bar';

// RXJS
import { debounceTime, distinctUntilChanged, switchMap, filter } from 'rxjs';

// Eigene Dialog-Komponente
import { EditFieldDialog } from '../edit-field-dialog/edit-field-dialog.component';

@Component({
  selector: 'app-steckbrief',
  standalone: true,
  imports: [
    CommonModule, ReactiveFormsModule, MatFormFieldModule, MatInputModule,
    MatAutocompleteModule, MatCardModule, MatButtonModule, MatIconModule, MatDialogModule
  ],
  templateUrl: './steckbrief.html',
  styleUrls: ['./steckbrief.css']
})
export class PersonSteckbriefComponent implements OnInit {
  private http = inject(HttpClient);
  private dialog = inject(MatDialog);
  private snackBar = inject(MatSnackBar);

  // Daten-Signals
  steckbriefData = signal<any>(null);
  foundPersons = signal<any[]>([]);
  foundParents = signal<any[]>([]);

  // Form Controls
  searchControl = new FormControl('');
  parentSearchCtrl = new FormControl('');

  // Getrennte Edit-Modi für Eltern
  isEditingFather = signal<boolean>(false);
  isEditingMother = signal<boolean>(false);

  ngOnInit() {
    // Hauptsuche
    this.searchControl.valueChanges.pipe(
      debounceTime(300),
      distinctUntilChanged(),
      filter(val => typeof val === 'string' && val.length > 1),
      switchMap(query => this.http.get<any[]>(`/api/personen/search/?q=${query}`))
    ).subscribe(res => this.foundPersons.set(res));

    // Suche für Eltern-Zuordnung
    this.parentSearchCtrl.valueChanges.pipe(
      debounceTime(300),
      distinctUntilChanged(),
      filter(val => typeof val === 'string' && val.length > 1),
      switchMap(query => this.http.get<any[]>(`/api/personen/search/?q=${query}`))
    ).subscribe(res => this.foundParents.set(res));
  }

  loadSteckbrief(id: number) {
    this.http.get<any>(`/api/personen/${id}/steckbrief/`).subscribe({
      next: (data) => this.steckbriefData.set(data),
      error: () => this.snackBar.open('Fehler beim Laden', 'OK')
    });
  }

  onPersonSelected(event: any) {
    const p = event.option.value;
    if (p && p.id) {
      this.loadSteckbrief(p.id);
      this.searchControl.setValue('', { emitEvent: false });
    }
  }

  displayFn(p: any): string {
    return p ? `${p.vorname} ${p.nachname}` : '';
  }

  navigateToPerson(id: number) {
    this.loadSteckbrief(id);
  }

  // --- Eltern-Logik ---

  toggleEditFather() {
    this.isEditingFather.update(v => !v);
    this.parentSearchCtrl.setValue('');
  }

  toggleEditMother() {
    this.isEditingMother.update(v => !v);
    this.parentSearchCtrl.setValue('');
  }

  setParent(role: 'vater_id' | 'mutter_id', parent: any) {
    this.updatePerson({ [role]: parent ? parent.id : null });
    if (role === 'vater_id') this.isEditingFather.set(false);
    if (role === 'mutter_id') this.isEditingMother.set(false);
    this.parentSearchCtrl.setValue('');
  }

  removeParent(role: 'vater_id' | 'mutter_id') {
    if (confirm('Zuordnung dieses Elternteils wirklich entfernen?')) {
      this.updatePerson({ [role]: null });
    }
  }

  // --- CRUD & Hilfsmethoden ---

  openEdit(fieldKey: string, currentValue: any, label: string) {
    const dialogRef = this.dialog.open(EditFieldDialog, {
      data: { title: `${label} bearbeiten`, value: currentValue, type: fieldKey.includes('datum') ? 'date' : 'text' }
    });

    dialogRef.afterClosed().subscribe(result => {
      if (result !== undefined) this.updatePerson({ [fieldKey]: result });
    });
  }

  updatePerson(payload: any) {
    const id = this.steckbriefData().person.id;
    this.http.put(`/api/personen/${id}/`, payload).subscribe(() => {
      this.loadSteckbrief(id);
      this.snackBar.open('Gespeichert', 'OK', { duration: 2000 });
    });
  }

  deletePerson() {
    if (confirm('Person wirklich löschen?')) {
      this.http.delete(`/api/personen/${this.steckbriefData().person.id}/`).subscribe(() => {
        this.steckbriefData.set(null);
        this.snackBar.open('Person gelöscht', 'OK');
      });
    }
  }


  openStammbaum(id: number) {
    // Öffnet das PDF direkt im Browser-Viewer eines neuen Tabs
    const url = `/api/stammbaum/${id}/pdf/?gen=3`;
    window.open(url, '_blank');
  }

}