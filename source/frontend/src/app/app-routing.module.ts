import { NgModule } from '@angular/core';
import { Routes, RouterModule } from '@angular/router';
import {SftpMainComponent} from './pages/sftp-main/sftp-main.component';

const routes: Routes = [
  { path: '', component: SftpMainComponent}
];

@NgModule({
  imports: [RouterModule.forRoot(routes)],
  exports: [RouterModule]
})
export class AppRoutingModule { }
