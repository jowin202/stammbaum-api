import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule, ReactiveFormsModule, FormGroup, FormBuilder, Validators } from '@angular/forms';
import { MatDialogModule, MatDialogRef } from '@angular/material/dialog';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatButtonModule } from '@angular/material/button';
import { MatSelectModule } from '@angular/material/select';

@Component({
  selector: 'app-new-person-dialog',
  standalone: true,
  imports: [
    CommonModule, FormsModule, ReactiveFormsModule, MatDialogModule, 
    MatFormFieldModule, MatInputModule, MatButtonModule, MatSelectModule
  ],
  template: `
    <h2 mat-dialog-title>Neue Person anlegen</h2>
    <mat-dialog-content [formGroup]="form">
      <div style="display: flex; flex-direction: column; gap: 15px; padding-top: 10px; min-width: 350px;">
        
        <mat-form-field appearance="outline">
          <mat-label>Vorname</mat-label>
          <input matInput formControlName="vorname" placeholder="z.B. Max">
        </mat-form-field>

        <mat-form-field appearance="outline">
          <mat-label>Nachname</mat-label>
          <input matInput formControlName="nachname" placeholder="z.B. Mustermann">
        </mat-form-field>

        <mat-form-field appearance="outline">
          <mat-label>Geschlecht</mat-label>
          <mat-select formControlName="geschlecht">
            <mat-option [value]="true">Männlich</mat-option>
            <mat-option [value]="false">Weiblich</mat-option>
            <mat-option [value]="null">Unbekannt</mat-option>
          </mat-select>
        </mat-form-field>

      </div>
    </mat-dialog-content>
    <mat-dialog-actions align="end">
      <button mat-button (click)="onCancel()">Abbrechen</button>
      <button mat-raised-button color="primary" [disabled]="form.invalid" (click)="onSave()">
        Erstellen
      </button>
    </mat-dialog-actions>
  `
})
export class NewPersonDialog {
  form: FormGroup;

  constructor(
    private fb: FormBuilder,
    private dialogRef: MatDialogRef<NewPersonDialog>
  ) {
    this.form = this.fb.group({
      vorname: ['', Validators.required],
      nachname: ['', Validators.required],
      geschlecht: [null]
    });
  }

  onCancel() {
    this.dialogRef.close();
  }

  onSave() {
    if (this.form.valid) {
      this.dialogRef.close(this.form.value);
    }
  }
}