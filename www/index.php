<?php

declare(strict_types=1);

use Tracy\Debugger;

require __DIR__ . '/../vendor/autoload.php';



// Tracy\Debugger::$logDirectory = dirname(__DIR__) . '/log';
$logDir = dirname(__DIR__) . '/log';   // /var/www/html/log
if (!is_dir($logDir)) {
    @mkdir($logDir, 0777, true);
}
Tracy\Debugger::enable(Tracy\Debugger::DEVELOPMENT);


Debugger::enable(Debugger::DEVELOPMENT, $logDir);
// опционально, чтобы писать всё даже в DEV:
Debugger::$logSeverity = E_ALL;

Debugger::log('probe: hello', 'exception');
$configurator = App\Bootstrap::boot();
$container = $configurator->createContainer();
$application = $container->getByType(Nette\Application\Application::class);
$application->run();
