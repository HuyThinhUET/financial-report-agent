Add-Type -AssemblyName System.Runtime.WindowsRuntime
[Windows.Media.Ocr.OcrEngine,Windows.Foundation,ContentType=WindowsRuntime] | Out-Null
[Windows.Storage.StorageFile,Windows.Storage,ContentType=WindowsRuntime] | Out-Null
[Windows.Graphics.Imaging.BitmapDecoder,Windows.Graphics.Imaging,ContentType=WindowsRuntime] | Out-Null
$script:asTask = [System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object { $_.Name -eq 'AsTask' -and $_.IsGenericMethod -and $_.GetParameters().Count -eq 1 -and $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1' } | Select-Object -First 1
function Await-Result($operation, $resultType) {
 $task = $script:asTask.MakeGenericMethod($resultType).Invoke($null, @($operation))
 $task.Wait()
 return $task.Result
}
$engine = [Windows.Media.Ocr.OcrEngine]::TryCreateFromUserProfileLanguages()
$items=Get-ChildItem -LiteralPath 'data/5-linh-vuc/trang-dau' -Filter '*.png'
foreach ($item in $items) {
 if (Test-Path -LiteralPath ([IO.Path]::ChangeExtension($item.FullName,'.ocr.txt'))) { continue }
 try {
  $file=Await-Result ([Windows.Storage.StorageFile]::GetFileFromPathAsync($item.FullName)) ([Windows.Storage.StorageFile])
  $stream=Await-Result ($file.OpenAsync([Windows.Storage.FileAccessMode]::Read)) ([Windows.Storage.Streams.IRandomAccessStream])
  $decoder=Await-Result ([Windows.Graphics.Imaging.BitmapDecoder]::CreateAsync($stream)) ([Windows.Graphics.Imaging.BitmapDecoder])
  $bitmap=Await-Result ($decoder.GetSoftwareBitmapAsync()) ([Windows.Graphics.Imaging.SoftwareBitmap])
  $result=Await-Result ($engine.RecognizeAsync($bitmap)) ([Windows.Media.Ocr.OcrResult])
  [IO.File]::WriteAllText([IO.Path]::ChangeExtension($item.FullName,'.ocr.txt'),$result.Text,[Text.UTF8Encoding]::new($false))
  $bitmap.Dispose(); $stream.Dispose()
 } catch { Write-Output ("ERROR " + $item.Name + ' ' + $_.Exception.Message) }
}
Write-Output "OCR completed: $($items.Count)"

