# PowerShell script to generate a 3.5 minute meeting audio using SAPI and SSML.
# Contains:
# - Speaker Introductions (Alice, Bob, Charlie)
# - Action Items (Tasks, owners, deadlines, priorities)
# - Sentiments (Positive, Neutral, Negative segments)
# - Pauses for speaker diarization

Add-Type -AssemblyName System.Speech
$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer

$outputPath = Join-Path -Path $PSScriptRoot -ChildPath "test_meeting.wav"
$synth.SetOutputToWaveFile($outputPath)

$ssml = @"
<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="en-US">
  <voice gender="female">
    Hello everyone. My name is Alice. I want to welcome you all to our quarterly review meeting. I am very happy to report that our previous marketing campaign was an excellent success. We achieved great results, and the customer engagement rate is awesome. The feedback from our early users has been extremely positive, and they love the new dashboard design. Let's keep up this great work as we transition into the next development cycle.
  </voice>
  <break time="3500ms"/>
  <voice gender="male">
    Hi Alice, I am Bob. Thank you for the positive update. It is indeed great news that the marketing campaign went so well. I have reviewed the core server metrics, and everything looks stable for now. However, we have a lot of new tasks to allocate. We need to begin planning our database architecture updates. We must ensure the system can scale as our user base grows.
  </voice>
  <break time="3500ms"/>
  <voice gender="female">
    Agreed. Bob, you must draft the new database design document by next Tuesday. It is crucial to have the schema ready so the backend team can review it.
  </voice>
  <break time="3500ms"/>
  <voice gender="male">
    Understood, Alice. I will draft the database design document by next Tuesday. I will make sure it covers all our scaling requirements. Also, when is our final deadline for the security audit?
  </voice>
  <break time="3500ms"/>
  <voice gender="female">
    Good question. We decided to schedule the final security audit for next Thursday morning. Charlie, please prepare the security logs before that.
  </voice>
  <break time="3500ms"/>
  <voice gender="male">
    Hi Alice, this is Charlie here. I need to report a critical problem. The backend latency has been very bad lately. We have a severe bottleneck in our query routing, which is a major issue. This is a critical risk for our deployment. It causes frequent timeout errors during peak hours, and we are getting negative feedback from our developers.
  </voice>
  <break time="3500ms"/>
  <voice gender="female">
    That sounds like a serious problem. Charlie, you must analyze the query routing latency issues by Friday. We cannot afford any delay.
  </voice>
  <break time="3500ms"/>
  <voice gender="male">
    Yes, I will analyze the query routing latency issues by Friday. I am confident we can find a perfect solution to solve it. I will work with the database team to check the queries.
  </voice>
  <break time="3500ms"/>
  <voice gender="female">
    Excellent. I also want to remind the team that we need to draft the user documentation. Bob, please complete the draft by tomorrow.
  </voice>
  <break time="3500ms"/>
  <voice gender="male">
    Got it, Alice. I will complete the user documentation draft by tomorrow.
  </voice>
  <break time="3500ms"/>
  <voice gender="female">
    Great! Let's close this session. Thank you everyone for your time. Have a perfect day.
  </voice>
</speak>
"@

Write-Host "Generating a 3.5-minute test meeting audio at: $outputPath ..."
$synth.SpeakSsml($ssml)
$synth.Dispose()
Write-Host "Success! Audio file generated. You can now upload 'test_meeting.wav' directly to the AI Meeting Assistant."
