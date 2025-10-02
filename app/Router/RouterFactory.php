<?php

declare(strict_types=1);

namespace App\Router;

use Nette;
use Nette\Application\Routers\RouteList;


final class RouterFactory
{
	use Nette\StaticClass;

	public static function createRouter(): RouteList
	{
		$router = new RouteList;
        $router->addRoute('test', 'Test:show');
		$router->addRoute('gemini/keywords', 'Gemini:keywords');
		$router->addRoute('/homepage/create', 'Homepage:create');
		$router->addRoute('/homepage/read', 'Homepage:read');
		$router->addRoute('/embeddings/control', 'Embeddings:control');
		
		
		$router->addRoute('<presenter>/<action>[/<id>]', 'Homepage:default');
		return $router;
	}
}  