import { NgModule, provideBrowserGlobalErrorListeners } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';
import { HttpClientModule, HTTP_INTERCEPTORS } from '@angular/common/http';
import { ReactiveFormsModule, FormsModule } from '@angular/forms';

import { AppRoutingModule } from './app-routing-module';
import { App } from './app';
import { Login } from './components/login/login';
import { Dashboard } from './components/dashboard/dashboard';
import { Cameras } from './components/cameras/cameras';
import { CameraForm } from './components/camera-form/camera-form';
import { CameraMonitor } from './components/camera-monitor/camera-monitor';
import { Processing } from './components/processing/processing';
import { Incidents } from './components/incidents/incidents';
import { IncidentDetail } from './components/incident-detail/incident-detail';
import { Evidence } from './components/evidence/evidence';
import { Alerts } from './components/alerts/alerts';
import { Navbar } from './components/navbar/navbar';
import { EvidenceModal } from './shared/evidence-modal/evidence-modal';
import { AuthInterceptor } from './core/interceptors/auth.interceptor';

@NgModule({
  declarations: [
    App,
    Login,
    Dashboard,
    Cameras,
    CameraForm,
    CameraMonitor,
    Incidents,
    IncidentDetail,
    Evidence,
    Alerts,
    Navbar,
    EvidenceModal
    ,Processing
  ],
  imports: [
    BrowserModule,
    AppRoutingModule,
    HttpClientModule,
    ReactiveFormsModule,
    FormsModule
  ],
  providers: [
    provideBrowserGlobalErrorListeners(),
    {
      provide: HTTP_INTERCEPTORS,
      useClass: AuthInterceptor,
      multi: true
    }
  ],
  bootstrap: [App]
})
export class AppModule { }

