<?php

//$username = "dropped";
//$password = "files";
//$server = "ftp.wrtdesign.com";
$path = $_GET['p'];
$filename = $_GET['f'];

$file_full = '/dropdir/'.$path."/".$filename;

//$file_path = "ftp://".$username.":".$password."@".$server."/".$file_full;

$fsize = filesize($file_path); 

header("Pragma: public");
header("Expires: 0");
header("Cache-Control: must-revalidate, post-check=0, pre-check=0");
header("Cache-Control: public");
header("Content-Description: File Transfer"); 
//header("Content-Type: $mtype");
header("Content-Type: application/octet-stream");
//header("Content-Disposition: attachment; filename=\"$asfname\""); */
header("Content-Disposition: attachment; filename=\"$filename\"");
header("Content-Transfer-Encoding: binary"); 
header("Content-Length: " . $fsize);


// download
// @readfile($file_path);
$file = @fopen($file_path,"rb");
if ($file) {
  while(!feof($file)) {
    print(fread($file, 1024*8));
    flush();
    if (connection_status()!=0) {
      @fclose($file);
      die();
    }
  }
  @fclose($file);
}

?>