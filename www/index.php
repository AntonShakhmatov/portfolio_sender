<?php

declare(strict_types=1);

use Tracy\Debugger;

require __DIR__ . '/../vendor/autoload.php';



Tracy\Debugger::$logDirectory = __DIR__ . '/../log';
Tracy\Debugger::enable(Tracy\Debugger::DEVELOPMENT);

$configurator = App\Bootstrap::boot();
$container = $configurator->createContainer();
$application = $container->getByType(Nette\Application\Application::class);
$application->run();
