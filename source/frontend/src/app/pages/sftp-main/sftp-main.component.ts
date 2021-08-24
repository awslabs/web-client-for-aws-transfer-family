import {Component, OnInit, ViewChild} from '@angular/core';
import {FtpService} from '../../service/ftp.service';
import {TreeNode} from 'primeng/api';
import {LoggerService} from '../../service/logger.service';
import {MenuItem, Message, MessageService} from 'primeng/api';
// import {FilterUtils} from 'primeng/utils';
import {SplitAreaDirective, SplitComponent} from 'angular-split';
import {AppConfig} from '../../service/app.config';
import {Title} from "@angular/platform-browser";
import { Table } from 'primeng/table';


@Component({
  selector: 'app-sftp-main',
  templateUrl: './sftp-main.component.html',
  styleUrls: ['./sftp-main.component.css']
})
export class SftpMainComponent implements OnInit {

  @ViewChild('split', { static: false }) split: SplitComponent;
  @ViewChild('area1', { static: false }) area1: SplitAreaDirective;
  @ViewChild('area2', { static: false }) area2: SplitAreaDirective;
  @ViewChild('dt') dt: Table | undefined;

  cols: any[];
  login_error:any;
  site_name:any;
  tag_line:any;
  site_title:any;
  uploadedFiles: any[] = [];
  loading: boolean = true;
  loading_table: boolean = false;
  file_downloading: boolean = false;
  items: MenuItem[];
  home: MenuItem;
  msgs: Message[] = [];
  parentNodes: TreeNode[];
  selectedTreeNode: TreeNode;
  currentFolderPath: string;
  filesForPath: any;
  progressValue: number = 0;
  progressContinue: boolean = false;
  selectedFile: any;
  displayRenameDialog = false;
  displayFolderDialog = false;
  renameInputText: string;
  newFolderInputText: string;
  current_folder: any;
  isConnected = false;
  submitted = false;
  username: string;
  password: string;
  ftpURL: string;
  myfiles: any;
  page: any;
  isConnectionTested = false;
  connError = false;
  health_ok = false;
  file_uploading = false;
  login_process = false
  direction: string = 'horizontal';
  upload_dialog_display: boolean = false;
  connect_dialog_display: boolean = false;
  numfiles_upload = 0;

  /**
   * Determines of the delete folder button is enabled;
   */
  btnDeleteFolderDisabled = true;

  /**
   * We disable the delete folder button if we detect child folders within the selected node.
   */
  childFolderDetected = true;

  /**
   * We disable the delete folder button if we detect child files within the selected node.
   */
  childFileDetected = true;


  getDocIcon(name){
    let icons= {
      "doc":"fa-file-word",
      "pdf":"fa-file-pdf",
      "docx":"fa-file-word",
      "xls":"fa-file-excel",
      "xlsx":"fa-file-excel",
      "ppt":"fa-file-powerpoint",
      "jpeg":"fa-image",
      "jpg":"fa-image",
      "JPEG":"fa-image",
      "png":"fa-image",
      "mp4":"fa-video",
      "mov":"fa-video",
      "avi":"fa-video"
    };
    let ext= name.split('.');
    ext=ext[ext.length-1];
    if(ext in icons){
      return icons[ext]
    }
    return "fa-file-alt";
  }

  getDocIconColor(name){
    let icons= {
      "doc":"blue",
      "pdf":"orange",
      "docx":"blue",
      "xls":"green",
      "xlsx":"green",
      "ppt":"red",
      "jpeg":"orange",
      "jpg":"orange",
      "JPEG":"orange",
      "png":"orange",
      "mp4":"orange",
      "mov":"orange",
      "avi":"orange"
    };
    let ext= name.split('.');
    ext=ext[ext.length-1];
    if(ext in icons){
      return icons[ext]
    }
    return "indigo";
  }

 

  showUploadDialog() {
    this.upload_dialog_display = true;
  }

 

  showConnectPage() {
    this.isConnectionTested = false;
    this.connError = false;
    this.page = 'settings';
  }


  showBrowsePage() {
    this.page = 'browse';
    this.timeout();
  }




  constructor(private sftpService: FtpService,
    private messageService: MessageService,
    private logger: LoggerService, private titleService: Title) { }




  onSubmit() {
    this.login_process = true;
    this.sftpService.checkConnection(this.ftpURL, this.username, this.password).subscribe(res => {
      this.login_error = null;
      this.isConnectionTested = true;
      this.login_process = false;
      this.ngOnInit();
    },
      error => {
        this.login_error = error.error.message;
        this.login_process = false;
        this.isConnectionTested = false;
        this.connError = true;
        this.sftpService.logout().subscribe((result) => {
          this.page = 'settings';
          this.username = '';
          this.password = '';
          this.health_ok = false;
          this.isConnected = false;
          location.reload();
        });
      }
    );
  }

  deleteConnection() {
    this.sftpService.logout().subscribe((result) => {
      this.page = 'settings';
      this.username = '';
          this.password = '';
      this.health_ok = false;
      this.isConnected = false;
      this.connError = false;
      this.isConnectionTested = false;
      this.currentFolderPath = null;
      this.login_process = false;
      location.reload();
    });
  }

  timeout() {
    setTimeout(() => {
      this.sftpService.isConnected().subscribe((result) => {
        if (this.page != 'settings') {
          this.page = 'browse';
          this.timeout();
        }
        this.health_ok = true;
      },
        (error) => {
          this.page = 'settings';
          this.health_ok = false;
        });

    }, 5000);
  }

  ngOnInit() {


    try{
    this.site_name = AppConfig.settings.company_name.name;
    this.tag_line= AppConfig.settings.tagline.tagline;
    console.log(AppConfig.settings);
    this.titleService.setTitle(AppConfig.settings.site_title.title);
    }
    catch (error){

      console.log(error);

    }
    this.sftpService.isConnected().subscribe((result) => {
      this.page = 'browse';
      this.isConnected = true;
      this.initFolders();
      this.health_ok = true;
      this.timeout();
    },
      (error) => {
        this.page = 'settings';
        this.isConnected = false;
        this.health_ok = false;
      });
  }

  initFolders() {

    this.loadParentNodes();
    // FilterUtils['custom'] = (value, filter): boolean => {
    //   if (filter === undefined || filter === null || filter.trim() === '') {
    //     return true;
    //   }

    //   if (value === undefined || value === null) {
    //     return false;
    //   }

    //   return value.includes(filter);
    // }

    this.cols = [
      { field: 'name', header: 'File Name', filterMatchMode: 'custom' },
      { field: 'type', header: 'File Type', filterMatchMode: 'custom' },
      { field: 'size', header: 'File Size', filterMatchMode: 'custom' }
    ];

    this.items = [
    ];

    this.home = { icon: 'pi pi-home' };

  }

  getFileSize(size){
    var sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    var bytes = size*1024;
    if (bytes == 0) return '0 B';
    var i = Math.floor(Math.log(bytes) / Math.log(1024));
    return Math.round(bytes / Math.pow(1024, i)) + ' ' + sizes[i];
  }


  onFolderPathExpand(event) {
    event.node.expanded = true;

    this.loading = true;

    this.selectedFile = null;
    if (event.node) {

      const input = {
        node_name: event.node.data,
        node_type: 'folder'
      };

      this.sftpService.getChildNodes(input).subscribe(nodes => {


        const data = nodes['data'];

        // if we have child nodes we disable delete
        this.childFolderDetected = data.length > 0;
        this.disableDeleteFolderButton();

        data.forEach(element => {

          element.collapsedIcon = "fas fa-folder";
          element.expandedIcon = "fas fa-folder-open";
          element.icon = "";
        });
        event.node.children = data;
        this.loading = false;
      });
    }
  }

  /**
   * Method to enable/disable delete folder button.
   */
  disableDeleteFolderButton() {
    this.btnDeleteFolderDisabled = this.childFileDetected || this.childFolderDetected;
  }

  onBreadCrumbClick = (event) => {


    var current_nodes = this.parentNodes;

    var item_paths = event.item.id.substring(2).split('/');

    item_paths[0] = '/' + item_paths[0];

    var cur_string = "";

    var cur_node = null;

    item_paths.forEach(element => {

      cur_string = cur_string + "/" + element;

      try {
        current_nodes.forEach(node => {
          if (node.data == cur_string) {
            cur_node = node;
            current_nodes = node.children;
            throw Error;
          }
        });
      }
      catch (e) {

      }

    });


    var e = {};

    e["node"] = cur_node;

    this.onFolderPathSelect(e);


  };


  onFolderPathSelect(event) {


    this.loading_table = true;

    if (event.node) {

      this.items = [];

      this.selectedFile = null;
      this.currentFolderPath = event.node.data;

      var bread = this.currentFolderPath.substring(2).split("/");

      var path = "/"

      var bc_nodes = [];

      bread.forEach(element => {
        path = path + "/" + element;
        this.items.push({ 'label': element, 'id': path });
      });

      this.current_folder = this.items[this.items.length - 1];

      const input = {
        node_name: event.node.data,
        node_type: 'file'
      };

      this.progressValue = 0;
      this.progressContinue = true;

      const self = this;
      this.selectedTreeNode = event.node as TreeNode;

      this.sftpService.getChildNodes(input).subscribe(nodes => {

        this.filesForPath = nodes['data'];

        // if we have child nodes we disable delete
        this.childFileDetected = nodes['data'].length > 0;
        this.disableDeleteFolderButton();

        this.progressContinue = false;

        this.progressValue = 0;

        this.loading_table = false;

        this.onFolderPathExpand(event);

      });
    }
  }

 


  selectFileForDownload(rowData) {

    const filePath = this.currentFolderPath + '/' + rowData.name;

    this.file_downloading = true;

    this.sftpService.downloadFile({ path: filePath })
      .subscribe((data) => {
        const blob = new Blob([(data)]);
        const downloadURL = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = downloadURL;
        link.download = rowData.name;
        link.click();
        this.file_downloading = false;
      },
      err => {
        this.messageEmit('error', 'Error downloading file', err.error.message+" Status: "+err.error.status, 2000);      
       });
  }

  displayRenameFileDialog(rowData) {
    this.displayRenameDialog = true;
  }


  displayNewFolderDialog() {
    this.displayFolderDialog = true;
  }


  connCheck() {
    this.sftpService.checkConnection(this.ftpURL, this.username, this.password).subscribe(res => {
      this.isConnectionTested = true;
    },
      error => {
        this.connError = true;
      }
    );
  }

  uploadFile(event, fileUploader): void {

    if (event.files.length == 0) {
      this.messageEmit('info', 'Upload File', 'Please select a file to upload.', 2000);
      return;
    }

    let fileToUpload = event.files[0];
    let formData = new FormData();
    formData.append('filetoupload', fileToUpload);
    formData.append('file_path', this.currentFolderPath);
    formData.append('file_name', fileToUpload.name);

    fileUploader.clear();
    this.file_uploading = true;
    this.messageService.clear();
    this.numfiles_upload = this.numfiles_upload+1;
    this.messageService.add({ severity: 'info', summary: 'File Upload:', detail: "Uploading "+ this.numfiles_upload+" files. Please wait ... " });
    this.sftpService.uploadFile(formData).subscribe(res => {
      this.file_uploading = false;
      this.onFolderPathSelect({ 'node': this.selectedTreeNode });
      fileUploader.clear();
      this.upload_dialog_display = false;
      this.numfiles_upload = this.numfiles_upload-1;
      if(this.numfiles_upload <=0){
        this.messageService.clear();
        this.messageEmit('success', 'File Upload:', 'Your file were successfully uploaded.', 2000);
      }else{
        this.messageService.clear();
        this.messageService.add({ severity: 'info', summary: 'File Upload:', detail: "Uploading "+ this.numfiles_upload+" files. Please wait ... " });
      }
    },
    err => {
      fileUploader.clear();
      this.upload_dialog_display = false;
      this.messageEmit('error', 'Error uploading file. ', err.error.message, null);
      this.messageService.clear();
      this.numfiles_upload =0;
     }
    );

  }

  onUpload(event) {
    for (const file of event.files) {
      this.uploadedFiles.push(file);
    }
  }

 
  applyFilterGlobal($event, stringVal) {
    this.dt.filterGlobal(($event.target as HTMLInputElement).value, 'contains');
  }

  newFolderCreate() {
    const filePath = this.currentFolderPath;
    const newFilePath = filePath + '/' + this.newFolderInputText;
    const input = {
      new_node_path: newFilePath,
      node_type: 'folder',
      node_name: this.newFolderInputText
    };

    this.sftpService.createFolder(input).subscribe(
      res => {
        this.logger.log('created folder: ' + JSON.stringify(res));
        this.displayFolderDialog = false;

        let new_node = {
          collapsedIcon: "fas fa-folder",
          data: newFilePath,
          expandedIcon: "fas fa-folder-open",
          icon: "",
          key: newFilePath,
          label: this.newFolderInputText,
          leaf: false
        } as TreeNode;
        this.selectedTreeNode.children.push(new_node);
        this.onFolderPathSelect({node: new_node});
        this.selectedTreeNode.expanded = true;
        
        this.newFolderInputText = '';

        this.messageService.add({ severity: 'success', summary: 'Folder Actions.', detail: 'Your folder was successfully created.' });
        setTimeout(() => {
          this.messageService.clear();
        }, 2000);

      },
      err => {
        this.messageService.add({ severity: 'error', summary: 'Something went wrong while creating the folder', detail: err.error.message+" Status: "+err.error.status });
        this.logger.error('Error creating folder: ' + JSON.stringify(err.error.message));
        setTimeout(() => {
          this.messageService.clear();
        }, 2000);
      },
      () => this.logger.log('creating folder operation completed.')
    );
  }

  /**
   * DOESNT LOOK USED - TODO: REMOVE
   */
  renameFileSubmit() {

    this.displayRenameDialog = false;

    const currentPath = this.currentFolderPath + '/' + this.selectedFile.name;
    const newPath = this.currentFolderPath + '/' + this.renameInputText;

    const input = {
      current_path: currentPath,
      new_path: newPath,
      node_type: 'file'
    };

    this.sftpService.renameFile(input).subscribe((data: any) => {
      this.renameInputText = '';
      this.selectedFile['data'] = data.new_path;
      this.selectedFile['name'] = data.new_name;
    });

  }

  deleteFile(rowData) {

    const filePath = this.currentFolderPath + '/' + rowData.name;

    const input = {
      node_name: filePath,
      node_type: 'file'
    };

    this.sftpService.deleteNode(input).subscribe((data) => {
      this.selectedFile = null;
      this.messageEmit('success', 'File Delete:', 'File deleted successfully', 2000);
      this.onFolderPathSelect({ 'node': this.selectedTreeNode });
    });

    this.selectedFile = null;

  }

  messageEmit(severity, summary, detail, timeout){
    this.messageService.add({ severity: severity, summary: summary, detail: detail });
    if(timeout != null){
      setTimeout(() => {
        this.messageService.clear();
      }, timeout); 
    }
    
  }

  deleteFolder() {
    let filePath = this.currentFolderPath;
    let cur_parent = this.selectedTreeNode.parent;

    let input = {
      node_name: filePath,
      node_type: 'folder'
    };
    this.sftpService.deleteNode(input).subscribe(
      res => {
        this.messageEmit('success', 'Folder Actions', 'Folder was successfully deleted', 2000);
        this.onFolderPathSelect({ 'node': cur_parent });
      },
      err => {
        this.messageEmit('error', 'Error deleting folder', err.error.message+" Status: "+err.error.status, 2000);      
        this.logger.error('Error creating folder: ' + JSON.stringify(err.error.message));
       },
      () => this.logger.log('HTTP deleting file operation completed')
    );
  }


  loadParentNodes() {

    this.loading = true;

    const input = {
      node_name: '/',
      node_type: 'folder'
    };

    this.sftpService.getChildNodes(input).subscribe((response: any) => {
      const data = response.data;

      data.forEach(element => {
        element.collapsedIcon = "fas fa-folder";
        element.expandedIcon = "fas fa-folder-open";
        element.icon = "";
      });
      this.parentNodes = data as TreeNode[];
      this.loading = false;
    });
  }


  onEditInit(event): void {

  }


  onEditCancel(event): void {

  }


  onEditComplete(event): void {
    var current_path = event.data.data;
    var new_file_name = event.data.name;
    var tokens = current_path.split('/');
    tokens[tokens.length - 1] = new_file_name;
    var new_path = tokens.join("/");
    var input = {};
    input["node_type"] = 'file';
    input["current_path"] = current_path;
    input["new_path"] = new_path;
    input["file_name"] = new_file_name;

    this.sftpService.renameFile(input).subscribe(
        res => {

        },
        err => {
          this.messageEmit('error', 'Error renaming file', err.error.message + ' Status: ' + err.error.status, 2000);
          this.logger.error('Error renaming file: ' + JSON.stringify(err.error.message));
        },
        () => this.logger.log('HTTP renaming file operation completed')
    );

  }

  expandAll() {
    this.parentNodes.forEach(node => {
      this.expandRecursive(node, true);
    });
  }

  private expandRecursive(node: TreeNode, isExpand: boolean) {
    node.expanded = isExpand;
    if (node.children) {
      node.children.forEach(childNode => {
        this.expandRecursive(childNode, isExpand);
      });
    }
  }

}
