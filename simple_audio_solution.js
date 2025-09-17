/**
 * Simple Google Apps Script for Audio in Google Sheets
 * This creates a popup audio player that stays within the sheet context
 */

function onOpen() {
  const ui = SpreadsheetApp.getUi();
  ui.createMenu('🎵 Audio Controls')
    .addItem('Play Audio (Selected Row)', 'playRowAudio')
    .addItem('Open Audio Dashboard', 'openAudioDashboard')
    .addToUi();
}

function playRowAudio() {
  const sheet = SpreadsheetApp.getActiveSheet();
  const activeRange = sheet.getActiveRange();
  const row = activeRange.getRow();
  
  if (row <= 1) {
    SpreadsheetApp.getUi().alert('Please select a row with audio data');
    return;
  }
  
  // Get the audio link from column E
  const audioCell = sheet.getRange(row, 5);
  const audioValue = audioCell.getValue();
  
  // Extract file ID from Google Drive link
  const fileIdMatch = audioValue.match(/\/d\/([a-zA-Z0-9_-]+)/);
  if (!fileIdMatch) {
    SpreadsheetApp.getUi().alert('No valid audio link found in this row');
    return;
  }
  
  const fileId = fileIdMatch[1];
  const audioUrl = `https://drive.google.com/uc?export=download&id=${fileId}`;
  
  // Get submission details
  const name = sheet.getRange(row, 1).getValue();
  const phone = sheet.getRange(row, 3).getValue();
  const status = sheet.getRange(row, 9).getValue() || 'Pending';
  
  // Create audio player popup
  const html = HtmlService.createHtmlOutput(`
    <!DOCTYPE html>
    <html>
    <head>
      <base target="_top">
      <style>
        body { 
          font-family: Arial, sans-serif; 
          padding: 20px; 
          background: #f5f5f5;
          margin: 0;
        }
        .player-container {
          background: white;
          border-radius: 10px;
          padding: 20px;
          box-shadow: 0 2px 10px rgba(0,0,0,0.1);
          max-width: 500px;
        }
        .submission-info {
          background: #e8f0fe;
          padding: 15px;
          border-radius: 5px;
          margin-bottom: 20px;
        }
        .audio-player {
          width: 100%;
          height: 60px;
          margin: 15px 0;
        }
        .controls {
          display: flex;
          gap: 10px;
          margin: 15px 0;
          flex-wrap: wrap;
        }
        .btn {
          background: #4285f4;
          color: white;
          border: none;
          padding: 10px 15px;
          border-radius: 5px;
          cursor: pointer;
          font-size: 14px;
        }
        .btn:hover { background: #3367d6; }
        .btn.approve { background: #34a853; }
        .btn.reject { background: #ea4335; }
        .status {
          font-weight: bold;
          color: #666;
        }
        .close-btn {
          position: absolute;
          top: 10px;
          right: 15px;
          background: #666;
          color: white;
          border: none;
          border-radius: 50%;
          width: 30px;
          height: 30px;
          cursor: pointer;
        }
      </style>
    </head>
    <body>
      <div class="player-container">
        <button class="close-btn" onclick="google.script.host.close()">×</button>
        
        <h2>🎵 Audio Player</h2>
        
        <div class="submission-info">
          <h3>${name}</h3>
          <p><strong>Phone:</strong> ${phone}</p>
          <p><strong>Status:</strong> <span class="status">${status}</span></p>
        </div>
        
        <audio controls class="audio-player" id="audioPlayer" preload="auto">
          <source src="${audioUrl}" type="audio/mpeg">
          <source src="${audioUrl}" type="audio/ogg">
          Your browser does not support the audio element.
        </audio>
        
        <div class="controls">
          <button class="btn" onclick="playAudio()">▶️ Play</button>
          <button class="btn" onclick="pauseAudio()">⏸️ Pause</button>
          <button class="btn" onclick="stopAudio()">⏹️ Stop</button>
          <button class="btn approve" onclick="updateStatus('approved')">✅ Approve</button>
          <button class="btn reject" onclick="updateStatus('rejected')">❌ Reject</button>
        </div>
        
        <p><small>💡 Tip: This player stays open while you work in the sheet</small></p>
      </div>
      
      <script>
        const audio = document.getElementById('audioPlayer');
        
        function playAudio() {
          audio.play().catch(e => console.log('Play failed:', e));
        }
        
        function pauseAudio() {
          audio.pause();
        }
        
        function stopAudio() {
          audio.pause();
          audio.currentTime = 0;
        }
        
        function updateStatus(status) {
          google.script.run
            .withSuccessHandler(() => {
              alert('Status updated to: ' + status);
              // Refresh the page to show updated status
              location.reload();
            })
            .updateStatus(${row}, status);
        }
        
        // Auto-play when loaded
        audio.addEventListener('loadeddata', () => {
          audio.play().catch(e => console.log('Auto-play failed:', e));
        });
      </script>
    </body>
    </html>
  `)
  .setTitle('🎵 Audio Player - ' + name)
  .setWidth(600)
  .setHeight(400);
  
  SpreadsheetApp.getUi().showModalDialog(html, 'Audio Player');
}

function openAudioDashboard() {
  // Get all submissions
  const sheet = SpreadsheetApp.getActiveSheet();
  const data = sheet.getDataRange().getValues();
  
  let html = `
    <!DOCTYPE html>
    <html>
    <head>
      <base target="_top">
      <style>
        body { font-family: Arial, sans-serif; padding: 20px; background: #f5f5f5; }
        .submission { 
          background: white; 
          margin: 15px 0; 
          padding: 20px; 
          border-radius: 10px; 
          box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        .audio-player { width: 100%; height: 50px; margin: 10px 0; }
        .btn { 
          background: #4285f4; 
          color: white; 
          border: none; 
          padding: 8px 15px; 
          border-radius: 5px; 
          cursor: pointer; 
          margin: 5px;
        }
        .btn:hover { background: #3367d6; }
        .status { font-weight: bold; }
        .pending { color: #f39c12; }
        .approved { color: #27ae60; }
        .rejected { color: #e74c3c; }
      </style>
    </head>
    <body>
      <h1>🎵 All Audio Submissions</h1>
  `;
  
  // Process each row (skip header)
  for (let i = 1; i < data.length; i++) {
    const row = data[i];
    if (row[0]) { // If name exists
      const name = row[0];
      const phone = row[2] || '';
      const status = row[8] || 'Pending';
      
      // Extract file ID from audio link
      const audioValue = row[4] || '';
      const fileIdMatch = audioValue.match(/\/d\/([a-zA-Z0-9_-]+)/);
      
      if (fileIdMatch) {
        const fileId = fileIdMatch[1];
        const audioUrl = `https://drive.google.com/uc?export=download&id=${fileId}`;
        
        html += `
          <div class="submission">
            <h3>${name}</h3>
            <p><strong>Phone:</strong> ${phone}</p>
            <p><strong>Status:</strong> <span class="status ${status.toLowerCase()}">${status}</span></p>
            
            <audio controls class="audio-player">
              <source src="${audioUrl}" type="audio/mpeg">
              Your browser does not support the audio element.
            </audio>
            
            <div>
              <button class="btn" onclick="updateStatus(${i}, 'approved')">✅ Approve</button>
              <button class="btn" onclick="updateStatus(${i}, 'rejected')">❌ Reject</button>
            </div>
          </div>
        `;
      }
    }
  }
  
  html += `
      <script>
        function updateStatus(row, status) {
          google.script.run
            .withSuccessHandler(() => {
              alert('Status updated to: ' + status);
              location.reload();
            })
            .updateStatus(row, status);
        }
      </script>
    </body>
    </html>
  `;
  
  const htmlOutput = HtmlService.createHtmlOutput(html)
    .setTitle('🎵 Audio Dashboard')
    .setWidth(800)
    .setHeight(600);
  
  SpreadsheetApp.getUi().showModalDialog(htmlOutput, 'Audio Dashboard');
}

function updateStatus(row, status) {
  const sheet = SpreadsheetApp.getActiveSheet();
  const statusColumn = 9; // Column I
  sheet.getRange(row + 1, statusColumn).setValue(status);
  
  // Add timestamp
  const timestampColumn = 10; // Column J  
  sheet.getRange(row + 1, timestampColumn).setValue(new Date());
}
