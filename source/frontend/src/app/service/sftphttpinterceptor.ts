import { Injectable, Inject } from "@angular/core";
import { tap } from "rxjs/operators";
import {
  HttpRequest,
  HttpHandler,
  HttpEvent,
  HttpInterceptor,
  HttpResponse,
  HttpErrorResponse,
  HttpXsrfTokenExtractor
} from "@angular/common/http";
import { Observable } from "rxjs";
import {DOCUMENT} from "@angular/common";

@Injectable()
export class MyInterceptor implements HttpInterceptor {
  constructor(@Inject(DOCUMENT) private doc: any,private tokenExtractor: HttpXsrfTokenExtractor) { }
  //function which will be called for all http calls
  intercept(
    request: HttpRequest<any>,
    next: HttpHandler
  ): Observable<HttpEvent<any>> {
  
        let requestToForward = request;
        let token = this.tokenExtractor.getToken() as string;
        var tokens= this.doc.cookie.split(";");
        tokens.forEach(element => {
          var csrf = element.split("=");
          if(csrf[0] == "csrf_access_token"){
            token = csrf[1];
          }
        });
        if (token !== null) {
            requestToForward = request.clone({ setHeaders: { "X-CSRF-TOKEN": token } });
        }
        return next.handle(requestToForward);
  }
}