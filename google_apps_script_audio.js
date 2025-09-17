/**
 * Google Apps Script for Audio Playback in Google Sheets
 * This creates a custom sidebar with audio controls
 */

function onOpen() {
  // Create custom menu
  const ui = SpreadsheetApp.getUi();
  ui.createMenu('🎵 Audio Player')
    .addItem('Open Audio Player', 'showAudioPlayer')
    .addItem('Play Selected Audio', 'playSelectedAudio')
    .addToUi();
}

function showAudioPlayer() {
  // Create HTML sidebar with audio player
  const html = HtmlService.createHtmlOutput(`
    <!DOCTYPE html>
    <html>
    <head>
      <base target="_top">
      <style>
        body { font-family: Arial, sans-serif; padding: 20px; }
        .audio-player { width: 100%; margin: 10px 0; }
        .submission { 
          border: 1px solid #ddd; 
          padding: 15px; 
          margin: 10px 0; 
          border-radius: 5px;
          background: #f9f9f9;
        }
        .play-btn { 
          background: #4285f4; 
          color: white; 
          border: none; 
          padding: 10px 20px; 
          border-radius: 5px; 
          cursor: pointer;
          margin: 5px;
        }
        .play-btn:hover { background: #3367d6; }
        .info { margin: 5px 0; }
        .status { font-weight: bold; }
      </style>
    </head>
    <body>
      <h2>🎵 Vocalist Audio Player</h2>
      <div id="audioContainer"></div>
      <button class="play-btn" onclick="loadSubmissions()">🔄 Refresh Submissions</button>
      
      <script>
        function loadSubmissions() {
          google.script.run
            .withSuccessHandler(displaySubmissions)
            .getAudioSubmissions();
        }
        
        function displaySubmissions(submissions) {
          const container = document.getElementById('audioContainer');
          container.innerHTML = '';
          
          submissions.forEach((submission, index) => {
            const div = document.createElement('div');
            div.className = 'submission';
            div.innerHTML = \`
              <h3>\${submission.name}</h3>
              <div class="info"><strong>Phone:</strong> \${submission.phone}</div>
              <div class="info"><strong>Address:</strong> \${submission.address}</div>
              <div class="info"><strong>Telegram:</strong> \${submission.telegram}</div>
              <div class="info"><strong>Status:</strong> <span class="status">\${submission.status}</span></div>
              
              <audio controls class="audio-player" id="audio\${index}">
                <source src="\${submission.audioUrl}" type="audio/mpeg">
                Your browser does not support the audio element.
              </audio>
              
              <div>
                <button class="play-btn" onclick="playAudio(\${index})">▶️ Play</button>
                <button class="play-btn" onclick="pauseAudio(\${index})">⏸️ Pause</button>
                <button class="play-btn" onclick="stopAudio(\${index})">⏹️ Stop</button>
                <button class="play-btn" onclick="updateStatus(\${submission.id}, 'approved')">✅ Approve</button>
                <button class="play-btn" onclick="updateStatus(\${submission.id}, 'rejected')">❌ Reject</button>
              </div>
            \`;
            container.appendChild(div);
          });
        }
        
        function playAudio(index) {
          const audio = document.getElementById('audio' + index);
          audio.play();
        }
        
        function pauseAudio(index) {
          const audio = document.getElementById('audio' + index);
          audio.pause();
        }
        
        function stopAudio(index) {
          const audio = document.getElementById('audio' + index);
          audio.pause();
          audio.currentTime = 0;
        }
        
        function updateStatus(id, status) {
          google.script.run
            .withSuccessHandler(() => {
              alert('Status updated to: ' + status);
              loadSubmissions();
            })
            .updateSubmissionStatus(id, status);
        }
        
        // Load submissions on page load
        loadSubmissions();
      </script>
    </body>
    </html>
  `)
  .setTitle('🎵 Audio Player')
  .setWidth(600);
  
  SpreadsheetApp.getUi().showSidebar(html);
}

function getAudioSubmissions() {
  // Get data from the sheet
  const sheet = SpreadsheetApp.getActiveSheet();
  const data = sheet.getDataRange().getValues();
  
  const submissions = [];
  
  // Skip header row
  for (let i = 1; i < data.length; i++) {
    const row = data[i];
    if (row[0]) { // If name exists
      // Extract file ID from the audio link
      let audioUrl = '';
      if (row[4] && row[4].includes('drive.google.com')) {
        // Extract file ID and create direct audio URL
        const match = row[4].match(/\/d\/([a-zA-Z0-9_-]+)/);
        if (match) {
          audioUrl = `https://drive.google.com/uc?export=download&id=${match[1]}`;
        }
      }
      
      submissions.push({
        id: i,
        name: row[0] || '',
        address: row[1] || '',
        phone: row[2] || '',
        telegram: row[3] || '',
        audioUrl: audioUrl,
        status: row[8] || 'Pending'
      });
    }
  }
  
  return submissions;
}

function playSelectedAudio() {
  // Play audio for the currently selected row
  const sheet = SpreadsheetApp.getActiveSheet();
  const range = sheet.getActiveRange();
  const row = range.getRow();
  
  if (row > 1) { // Skip header
    const audioCell = sheet.getRange(row, 5); // Column E
    const audioValue = audioCell.getValue();
    
    // Extract file ID and create audio URL
    const match = audioValue.match(/\/d\/([a-zA-Z0-9_-]+)/);
    if (match) {
      const audioUrl = `https://drive.google.com/uc?export=download&id=${match[1]}`;
      
      // Open audio in new tab (closest we can get to in-sheet playback)
      const html = `
        <!DOCTYPE html>
        <html>
        <head><title>Audio Player</title></head>
        <body>
          <h3>Playing: ${sheet.getRange(row, 1).getValue()}</h3>
          <audio controls autoplay style="width: 100%;">
            <source src="${audioUrl}" type="audio/mpeg">
            Your browser does not support the audio element.
          </audio>
          <p><a href="${audioUrl}" target="_blank">Open in new tab</a></p>
        </body>
        </html>
      `;
      
      const htmlOutput = HtmlService.createHtmlOutput(html)
        .setTitle('Audio Player')
        .setWidth(400)
        .setHeight(200);
      
      SpreadsheetApp.getUi().showModalDialog(htmlOutput, '🎵 Audio Player');
    }
  }
}

function updateSubmissionStatus(id, status) {
  // Update status in the sheet
  const sheet = SpreadsheetApp.getActiveSheet();
  const statusColumn = 9; // Column I
  sheet.getRange(id + 1, statusColumn).setValue(status);
  
  // Add timestamp
  const timestampColumn = 10; // Column J
  sheet.getRange(id + 1, timestampColumn).setValue(new Date());
}
