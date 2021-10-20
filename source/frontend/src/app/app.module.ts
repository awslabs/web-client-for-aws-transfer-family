import { BrowserModule } from '@angular/platform-browser';
import { NgModule } from '@angular/core';

import { AppRoutingModule } from './app-routing.module';
import { AppComponent } from './app.component';
import {FormsModule, ReactiveFormsModule} from '@angular/forms';

import {HttpClientModule, HTTP_INTERCEPTORS} from '@angular/common/http';
// import {XSRF_COOKIE_NAME, XSRF_HEADER_NAME} from '@angular/common/http/';
import { ButtonModule } from 'primeng/button';
import { TableModule } from 'primeng/table';
import { DialogModule } from 'primeng/dialog';
// import { AccordionMoule } from 'primeng/breadcrumb';

import {BrowserAnimationsModule} from '@angular/platform-browser/animations';
import { AngularSplitModule } from 'angular-split';

// import { MyInterceptor } from './service/sftphttpinterceptor';

// import {
//   AccordionModule,
//   AutoCompleteModule,
//   BreadcrumbModule,
//   CardModule,
//   CarouselModule,
//   ChartModule,
//   CheckboxModule,
//   ChipsModule,
//   CodeHighlighterModule,
//   ColorPickerModule,
//   ConfirmDialogModule,
//   ContextMenuModule,
//   DataViewModule,
//   DropdownModule,
//   EditorModule,
//   FieldsetModule, 
//   FileUploadModule,
//   FullCalendarModule,
//   GalleriaModule,
//   InplaceModule,
//   InputMaskModule,
//   InputSwitchModule,
//   InputTextareaModule,
//   InputTextModule,
//   LightboxModule,
//   ListboxModule,
//   MegaMenuModule,
//   MenubarModule,
//   MenuModule,
//   MessageModule, MessageService,
//   MessagesModule,
//   MultiSelectModule,
//   OrderListModule,
//   OrganizationChartModule,
//   OverlayPanelModule,
//   PaginatorModule,
//   PanelMenuModule,
//   PanelModule,
//   PasswordModule,
//   PickListModule,
//   ProgressBarModule, ProgressSpinnerModule,
//   RadioButtonModule,
//   RatingModule,
//   ScrollPanelModule,
//   SelectButtonModule,
//   SlideMenuModule,
//   SliderModule,
//   SpinnerModule, SplitButtonModule,
//   StepsModule,
//   TabMenuModule,
//   TabViewModule,
//   TerminalModule,
//   TieredMenuModule,
//   ToastModule,
//   ToggleButtonModule,
//   ToolbarModule,
//   TooltipModule,
//   TreeModule,
//   TreeTableModule,
//   VirtualScrollerModule
// } from 'primeng/';

// import {AppTopBarComponent} from './app.topbar.component';
// import {AppMenuComponent, AppSubMenuComponent} from './app.menu.component';
// import {AppFooterComponent} from './app.footer.component';

import { SftpMainComponent } from './pages/sftp-main/sftp-main.component';
import {MyInterceptor} from './service/sftphttpinterceptor';
import { APP_INITIALIZER } from '@angular/core';
import { AppConfig } from './service/app.config';
import {BreadcrumbModule} from 'primeng/breadcrumb';
import {TreeModule} from 'primeng/tree';
import {MessageModule} from 'primeng/message';
import {MessagesModule} from 'primeng/messages';
import {MessageService} from 'primeng/api';
import {FileUploadModule} from 'primeng/fileupload';
import {TooltipModule} from 'primeng/tooltip';



export function initializeApp(appConfig: AppConfig) {
  return () => appConfig.load();
}


@NgModule({
  imports: [
    AngularSplitModule.forRoot(),
    BrowserModule,
    AppRoutingModule,
    FormsModule,
    HttpClientModule,
    BrowserAnimationsModule,
    // AccordionModule,
    // AutoCompleteModule,
    BreadcrumbModule,
    ButtonModule,
    // CardModule,
    // CarouselModule,
    // ChartModule,
    // CheckboxModule,
    // ChipsModule,
    // CodeHighlighterModule,
    // ConfirmDialogModule,
    // ColorPickerModule,
    // ContextMenuModule,
    // DataViewModule,
    DialogModule,
    FileUploadModule,
    // DropdownModule,
    // EditorModule,
    // FieldsetModule,
    // FullCalendarModule,
    // GalleriaModule,
    // GrowlModule,
    // InplaceModule,
    // InputMaskModule,
    // InputSwitchModule,
    // InputTextModule,
    // InputTextareaModule,
    // LightboxModule,
    // ListboxModule,
    // MegaMenuModule,
    // MenuModule,
    // MenubarModule,
    MessageModule,
    MessagesModule,
    // MultiSelectModule,
    // OrderListModule,
    // OrganizationChartModule,
    // OverlayPanelModule,
    // PaginatorModule,
    // PanelModule,
    // PanelMenuModule,
    // PasswordModule,
    // PickListModule,
    // ProgressBarModule,
    // RadioButtonModule,
    // RatingModule,
    // ScrollPanelModule,
    // SelectButtonModule,
    // SlideMenuModule,
    // SliderModule,
    // SpinnerModule,
    // SplitButtonModule,
    // StepsModule,
    TableModule,
    // TabMenuModule,
    // TabViewModule,
    // TerminalModule,
    // TieredMenuModule,
    // ToastModule,
    // ToggleButtonModule,
    // ToolbarModule,
    TooltipModule,
    TreeModule,
    // TreeTableModule,
    // VirtualScrollerModule,
    ReactiveFormsModule,
    // FileUploadModule,
    // ProgressSpinnerModule
  ],
  declarations: [
    AppComponent,
    SftpMainComponent
  ],
  providers: [
    MessageService,
    {provide: HTTP_INTERCEPTORS, useClass: MyInterceptor, multi: true},
    AppConfig,
    { provide: APP_INITIALIZER,
      useFactory: initializeApp,
      deps: [AppConfig], multi: true }
  ],
  exports: [],
  bootstrap: [AppComponent]
})
export class AppModule { }
