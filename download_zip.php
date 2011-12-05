<?php
/* $username = "dropped"; */
/* $password = "files"; */
/* $server = "ftp.wrtdesign.com"; */

$files = $_GET['fa'];
$path = $_GET['p'];
$fullpath = '/dropdir/' . $path;
//$files = array($argv[1]);

$ra_zip = tempnam("tmp", "zip");

$zip = new ZipArchive();
$zip->open($ra_zip, ZipArchive::OVERWRITE);
foreach ($files as $file) {
    $zip->addFile($fullpath . '/' . $file, $file);
}
$zip->close();

$fsize = filesize($ra_zip);
//print $fsize;

//header("Pragma: public");
//header("Expires: 0");
//header("Cache-Control: must-revalidate, post-check=0, pre-check=0");
//header("Cache-Control: public");
//header("Content-Description: File Transfer"); 
header("Content-Type: application/zip");
header("Content-Disposition: attachment; filename=\"RemovedAttachments.zip\"");
//header("Content-Transfer-Encoding: binary"); 
header("Content-Length: " . $fsize);

ob_clean();
flush();

readfile($ra_zip);
unlink($ra_zip);
?>