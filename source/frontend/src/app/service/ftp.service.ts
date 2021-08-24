import { Injectable } from '@angular/core';

import {HttpClient, HttpHeaders, HttpClientXsrfModule} from '@angular/common/http';
import {LoggerService} from './logger.service';
import {Observable} from "rxjs";


@Injectable({
  providedIn: 'root'
})
export class FtpService {

  BASE_URL:any;

  constructor(
    private logger: LoggerService,
    private http: HttpClient
  ) {

      this.BASE_URL = 'REPLACE_ME';
   }


 

  deleteConnection(){
    localStorage.removeItem('username');
    localStorage.removeItem('password');
    localStorage.removeItem('ftpURL');
  }



  isConnected(){

    return  this.http.get(`${this.BASE_URL}/api/isconnected`, {withCredentials:true});

  }

  getSFTPCredentialsFromLocalStorage() {

    return [localStorage.getItem('username'), localStorage.getItem('ftpURL')];

  }

  getFTPURL() {

    console.log(localStorage.getItem('username'), localStorage.getItem('ftpUrl'));

    return localStorage.getItem('ftpURL');

  }

  checkConnection(url, username, password){

    const combined = username + ' ' + password;

    const headerDict = {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
      'Authorization': 'Basic ' + btoa(combined.replace(/['"]+/g, ''))
    }

    
    const requestOptions = {                                                                                                                                                                                 
      headers: new HttpHeaders(headerDict), 
      withCredentials:true
    };

    return this.http.post(`${this.BASE_URL}/api/authenticate`,{}, requestOptions);

   

  }

  uploadFile(input) {

    return this.http.post(`${this.BASE_URL}/api/upload`, input, {withCredentials:true});

  }

  downloadFile(input) {

    return this.http.post(`${this.BASE_URL}/api/download`, input,  {
      responseType: 'arraybuffer',
      withCredentials:true});

  }

  renameFile(input) {

    return this.http.post(`${this.BASE_URL}/api/rename`, input,  {withCredentials:true});

  }

  createFolder(input): Observable<any> {

    return this.http.post(`${this.BASE_URL}/api/createfolder`, input,  {
      withCredentials:true});

  }

  deleteNode(input) {

    return this.http.post(`${this.BASE_URL}/api/delete`, input,  {withCredentials:true});

  }

  getChildNodes(input) {
    console.log(`${this.BASE_URL}/api/listchildnodes`, this.BASE_URL);
    return this.http.post(`${this.BASE_URL}/api/listchildnodes`, input, {withCredentials:true});
  }

  logout() {
    return this.http.post(`${this.BASE_URL}/api/logout`, {},  {withCredentials:true});
  }

}
