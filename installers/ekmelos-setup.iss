; Inno Setup script for the Ekmelos font

[Setup]
AppId={{469FFC9C-9901-498D-8EE5-095628BF292D}
AppName="Ekmelos Font"
AppVersion="2.58"
; AppVerName="Ekmelos Font 2.58"
AppCopyright="Copyright (c) 2013-2024 by Thomas Richter (thomas-richter@aon.at)"
AppPublisher="Thomas Richter"
AppPublisherURL="http://www.ekmelic-music.org/"
AppSupportURL="https://github.com/tr-igem/ekmelos"
AppUpdatesURL="https://github.com/tr-igem/ekmelos"
DefaultDirName="{commoncf}\SMuFL\Fonts\Ekmelos"
DisableDirPage=no
DefaultGroupName="Ekmelos Font"
AllowNoIcons=yes
LicenseFile="..\LICENSE.txt"
OutputBaseFilename="ekmelos-setup"
Compression=lzma
SolidCompression=yes
UsePreviousAppDir=no

[Languages]
Name: "en"; MessagesFile: "compiler:Default.isl"
Name: "de"; MessagesFile: "compiler:Languages\German.isl"

[Messages]
en.SelectDirDesc=Where should the extra files of Ekmelos be installed?
en.SelectDirLabel3=Setup will install the extra files of Ekmelos into the following folder (and the subfolder metadata).
de.SelectDirDesc=Wo sollen die Extradateien von Ekmelos installiert werden?
de.SelectDirLabel3=Das Setup wird die Extradateien von Ekmelos in den folgenden Ordner (und den Unterordner metadata) installieren.

[Files]
Source: "..\metadata\classes.json"; DestDir: "{app}\metadata"; Flags: ignoreversion
Source: "..\metadata\glyphdata.json"; DestDir: "{app}\metadata"; Flags: ignoreversion
Source: "..\metadata\glyphnames.json"; DestDir: "{app}\metadata"; Flags: ignoreversion
Source: "..\metadata\metadata.json"; DestDir: "{app}\metadata"; Flags: ignoreversion
Source: "..\metadata\ekmelib.json"; DestDir: "{app}\metadata"; Flags: ignoreversion
Source: "..\metadata\ekmelily.json"; DestDir: "{app}\metadata"; Flags: ignoreversion
Source: "..\LICENSE.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\OFL-FAQ.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\docs\CHANGELOG.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\fonts\otf\Ekmelos.otf"; DestDir: "{fonts}"; FontInstall: "Ekmelos"; Flags: uninsneveruninstall fontisnttruetype
