import { TestBed } from '@angular/core/testing';

import { FtpService } from './ftp.service';

describe('FtpService', () => {
  let service: FtpService;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(FtpService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
