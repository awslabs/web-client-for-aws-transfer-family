import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { SftpMainComponent } from './sftp-main.component';

describe('SftpMainComponent', () => {
  let component: SftpMainComponent;
  let fixture: ComponentFixture<SftpMainComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ SftpMainComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(SftpMainComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
