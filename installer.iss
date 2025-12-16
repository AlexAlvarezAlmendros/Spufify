; Inno Setup Script for Spufify
; Requires: Inno Setup 6.0+ (https://jrsoftware.org/isinfo.php)

#define MyAppName "Spufify"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Alex Alvarez Almendros"
#define MyAppURL "https://github.com/AlexAlvarezAlmendros/Spufify"
#define MyAppExeName "Spufify.exe"

[Setup]
; App identification
AppId={{8F3D5E2A-7B9C-4E1D-9F6A-2C8B5D4E9A3F}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}/issues
AppUpdatesURL={#MyAppURL}/releases

; Installation paths
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes

; Output settings
OutputDir=dist\installer
OutputBaseFilename=Spufify-Setup-{#MyAppVersion}
SetupIconFile=assets\icon.ico
UninstallDisplayIcon={app}\{#MyAppExeName}

; Compression
Compression=lzma2/max
SolidCompression=yes

; Windows version requirements
MinVersion=10.0
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64

; Privileges
PrivilegesRequired=admin

; Wizard appearance
WizardStyle=modern
DisableWelcomePage=no

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"
Name: "startupicon"; Description: "Create Start Menu shortcut"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; Main application files (from PyInstaller build)
Source: "dist\Spufify\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

; FFmpeg (must be downloaded separately and placed in ffmpeg folder)
Source: "ffmpeg\ffmpeg.exe"; DestDir: "{app}\ffmpeg"; Flags: ignoreversion
Source: "ffmpeg\ffprobe.exe"; DestDir: "{app}\ffmpeg"; Flags: ignoreversion

; Documentation
Source: "README.md"; DestDir: "{app}"; Flags: ignoreversion isreadme
Source: "LICENSE"; DestDir: "{app}"; Flags: ignoreversion
Source: ".env.example"; DestDir: "{app}"; Flags: ignoreversion

[Dirs]
; Create output directory for recordings
Name: "{userappdata}\{#MyAppName}\Music"; Permissions: users-full

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
; Open configuration dialog after installation
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#MyAppName}}"; Flags: nowait postinstall skipifsilent

[Code]
var
  SpotifyConfigPage: TInputQueryWizardPage;

procedure InitializeWizard;
begin
  { Create custom page for Spotify API credentials }
  SpotifyConfigPage := CreateInputQueryPage(wpSelectTasks,
    'Spotify API Configuration',
    'Enter your Spotify Developer credentials',
    'To use Spufify, you need to create a Spotify Developer App at https://developer.spotify.com/dashboard' + #13#10 +
    'Set the Redirect URI to: http://127.0.0.1:8888/callback' + #13#10#13#10 +
    'You can skip this step and configure later by editing the .env file in the installation folder.');

  SpotifyConfigPage.Add('Client ID:', False);
  SpotifyConfigPage.Add('Client Secret:', True); { Password field }
  
  { Set default placeholder values }
  SpotifyConfigPage.Values[0] := 'your_client_id_here';
  SpotifyConfigPage.Values[1] := 'your_client_secret_here';
end;

function NextButtonClick(CurPageID: Integer): Boolean;
begin
  Result := True;
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  EnvFilePath: String;
  EnvContent: String;
  ClientID: String;
  ClientSecret: String;
begin
  if CurStep = ssPostInstall then
  begin
    { Create .env file with user's credentials }
    EnvFilePath := ExpandConstant('{app}\.env');
    
    ClientID := SpotifyConfigPage.Values[0];
    ClientSecret := SpotifyConfigPage.Values[1];
    
    { Build .env content }
    EnvContent := '# Spotify API Credentials' + #13#10;
    EnvContent := EnvContent + '# Get these from https://developer.spotify.com/dashboard' + #13#10;
    EnvContent := EnvContent + '# Set Redirect URI to: http://127.0.0.1:8888/callback' + #13#10 + #13#10;
    EnvContent := EnvContent + 'SPOTIPY_CLIENT_ID=' + ClientID + #13#10;
    EnvContent := EnvContent + 'SPOTIPY_CLIENT_SECRET=' + ClientSecret + #13#10;
    
    { Save to file }
    SaveStringToFile(EnvFilePath, EnvContent, False);
    
    { Add FFmpeg to PATH for current user }
    if RegWriteExpandStringValue(HKEY_CURRENT_USER, 'Environment', 'Path',
       ExpandConstant('{app}\ffmpeg;') + GetEnv('Path')) then
    begin
      Log('FFmpeg added to user PATH successfully');
    end
    else
    begin
      MsgBox('Warning: Could not add FFmpeg to PATH automatically. You may need to add it manually: ' + #13#10 +
             ExpandConstant('{app}\ffmpeg'), mbInformation, MB_OK);
    end;
  end;
end;

function InitializeUninstall(): Boolean;
begin
  Result := True;
  { Ask user if they want to keep recordings }
  if MsgBox('Do you want to delete your recorded music files?' + #13#10#13#10 +
            'Location: ' + ExpandConstant('{userappdata}\{#MyAppName}\Music'),
            mbConfirmation, MB_YESNO) = IDYES then
  begin
    DelTree(ExpandConstant('{userappdata}\{#MyAppName}'), True, True, True);
  end;
end;
