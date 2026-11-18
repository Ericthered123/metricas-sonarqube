# Manifiesto de `datos/`

Generado el 2026-11-18 con `guiones/manifiesto_datos.py`. No editar a mano.

Cada carpeta se cruza con `registro_analisis.csv` por la clave de SonarQube. Las carpetas `extraccion-*`, `pmd-*` y `diff-*` salen del release nuevo de cada proyecto (SCRUM-29 y PT3). Versiones de las herramientas en `VERSIONES.md`; perfiles, gate y parámetros de la instancia en `laboratorio/configuracion/`.

## `corpus-commons-collections/`

| Fecha | Versión | Commit | Perfil | Tests | JaCoCo | Resultado |
|---|---|---|---|---|---|---|
| 2026-10-13T16:12:57 | 4.5.0 | `7f7fb0244abc` | Sonar way comprehensive | sí | sí | ok |
| 2026-10-13T16:23:34 | 4.6.0 | `4107624de41a` | Sonar way comprehensive | sí | sí | ok (gate rechazado) |

| Archivo | Filas | SHA-256 |
|---|---|---|
| `codigo_nuevo_archivo.csv` | 368 | `6e440a87fd3c453ee5ab547f5f75fa5eafb1c9951c64dcfbf7d39c0545174d93` |
| `comparacion_codigo_nuevo.csv` | 677 | `a8441c113144cc6d476d9f6361db106739b2d4c8c035150e9a89ccc415667a5c` |
| `issues.csv` | 1584 | `3b045e09421c1dab5fb4f61ce20c3c5a64d4efc1c68b137cea780b6c83a7a2ed` |
| `medidas_archivo.csv` | 368 | `5d9eeea2039a8b3e2c92a91a3267aa9430c47a9d98f9ead7e71dcd8e0596a378` |
| `medidas_proyecto.csv` | 1 | `e73a985e51ee075b3857d5c355c1fb908c36420473ef11a126008ef47a0a321b` |
| `quality_gate.csv` | 4 | `b894bb9dfb099c938cb21752182439e6d53046ac3a69529289e8a3f9f9ba6a10` |

## `corpus-commons-io/`

| Fecha | Versión | Commit | Perfil | Tests | JaCoCo | Resultado |
|---|---|---|---|---|---|---|
| 2026-10-13T17:03:39 | 2.21.0 | `54073d3b5fdd` | Sonar way comprehensive | sí | sí | ok |
| 2026-10-13T17:22:52 | 2.22.0 | `c14acc16f73e` | Sonar way comprehensive | sí | sí | ok (gate rechazado) |

| Archivo | Filas | SHA-256 |
|---|---|---|
| `codigo_nuevo_archivo.csv` | 277 | `89645b8f2aecf3cb8d9a429c639cba441622dbd426f79646e7b73fecab99b03a` |
| `comparacion_codigo_nuevo.csv` | 370 | `ad63528950cf8bd403fe16dbfd4f3989947bf2aa84f97d7f96f47241aa55846b` |
| `issues.csv` | 1081 | `0dfd8a87c05dc93c6af6cfe057a6d3c725cf76c6a2360678c487a5ed28654e38` |
| `medidas_archivo.csv` | 277 | `504e58e5aab4071453b315edfef5d991023bf595ce29e7fc80b6209b39491fb1` |
| `medidas_proyecto.csv` | 1 | `571c58607333c7f085a5a9d997777e5f6073c5bdb5c540fe8717d27a8d6be40c` |
| `quality_gate.csv` | 4 | `a8d97b0339460359517143f7765cbda7f5a4dbc26dc3ff3d7907ea27132a0d7e` |

## `corpus-core-commons-collections/`

| Fecha | Versión | Commit | Perfil | Tests | JaCoCo | Resultado |
|---|---|---|---|---|---|---|
| 2026-10-13T16:38:33 | 4.5.0 | `7f7fb0244abc` | Sonar way core | sí | sí | ok |
| 2026-10-13T16:49:04 | 4.6.0 | `4107624de41a` | Sonar way core | sí | sí | ok (gate rechazado) |

| Archivo | Filas | SHA-256 |
|---|---|---|
| `codigo_nuevo_archivo.csv` | 368 | `2a79b71e56875005fb40bcfda36728c0ff5414467c143cb36ab0c596c1cfa8b4` |
| `comparacion_codigo_nuevo.csv` | 677 | `0cba54c5de988cbd133ff924ad62f494d7b2c78a8908eef0d373d7e63982ecbf` |
| `issues.csv` | 84 | `4b4747127fb0dda239bce00d20eb63ca631453e4e4bc3fbaf3a1f128349d2c35` |
| `medidas_archivo.csv` | 368 | `ba9308adb6fcb91689171de84bf7e3f209305739ac7ccab4074ce7173cc1520c` |
| `medidas_proyecto.csv` | 1 | `68a667807b13ef470e836b280995f8526680b516a55cbf25e0ff01a5fbafdcb4` |
| `quality_gate.csv` | 4 | `569c3fafd487287e8c285d025d18999e8a5cba9be2b6e8b9fd953ef8cfcb686b` |

## `corpus-core-commons-io/`

| Fecha | Versión | Commit | Perfil | Tests | JaCoCo | Resultado |
|---|---|---|---|---|---|---|
| 2026-10-13T17:43:18 | 2.21.0 | `54073d3b5fdd` | Sonar way core | sí | sí | ok |
| 2026-10-13T18:03:22 | 2.22.0 | `c14acc16f73e` | Sonar way core | sí | sí | ok (gate rechazado) |

| Archivo | Filas | SHA-256 |
|---|---|---|
| `codigo_nuevo_archivo.csv` | 277 | `102d7b54851285c141c0546691f7dfb8e63e91c74e7e831a85e4871812931785` |
| `comparacion_codigo_nuevo.csv` | 370 | `c40cdf099e8e577e19ef3d7b502aaa093d7f5a96ad2454e9d7d88a59a5415ea0` |
| `issues.csv` | 96 | `6581694ab7f46725c68c79a1011f19ca9c0db5d6ae5369482b14a4955352925f` |
| `medidas_archivo.csv` | 277 | `e425434e7fcaf188376efcb1359751d505ba0d73987e146707c6cebdbe5aef5f` |
| `medidas_proyecto.csv` | 1 | `b83548de185feece4a7713006e6a6f2d554fb8414c3efdf3836ff2b4c4fb6a0a` |
| `quality_gate.csv` | 4 | `42856d0ee8aba633f6698621262c42a8584914ac50b01f47712ce2e1ff978244` |

## `corpus-core-jfreechart/`

| Fecha | Versión | Commit | Perfil | Tests | JaCoCo | Resultado |
|---|---|---|---|---|---|---|
| 2026-10-13T15:48:24 | 1.5.5 | `cb8ff67d983b` | Sonar way core | sí | sí | ok |
| 2026-10-13T16:00:58 | 1.5.6 | `703427c2acf0` | Sonar way core | sí | sí | ok (gate rechazado) |

| Archivo | Filas | SHA-256 |
|---|---|---|
| `codigo_nuevo_archivo.csv` | 694 | `9b3cc77dc022526704f2c87180c3f8af2e414a5333b524cd33a07bba55d4970d` |
| `comparacion_codigo_nuevo.csv` | 1016 | `72c9122937749acb2bba96877866dfa668edcff49d0fb0aacaa3f2332661faca` |
| `issues.csv` | 434 | `b1fb7958fc426dd42579a4665cc77a109f67074f74618a91b9c5ff71e44d12f0` |
| `medidas_archivo.csv` | 694 | `ab5ff7d4325da3c953fbc767034441b50456f50ceb69eec652411b63decc6d05` |
| `medidas_proyecto.csv` | 1 | `a22ae44d2b471bf3fbdd9bef5e592962718c9336209d885735573cd9482a0ce9` |
| `quality_gate.csv` | 4 | `0b0b18e11d88f3b64fb7427acf19a4427043ee46d20771262255e157da0dc630` |

## `corpus-core-jsoup/`

| Fecha | Versión | Commit | Perfil | Tests | JaCoCo | Resultado |
|---|---|---|---|---|---|---|
| 2026-10-13T15:12:13 | 1.22.2 | `ac28afe6e5bf` | Sonar way core | sí | sí | ok |
| 2026-10-13T15:17:29 | 1.23.2 | `fbc7775c462f` | Sonar way core | sí | sí | ok (gate rechazado) |

| Archivo | Filas | SHA-256 |
|---|---|---|
| `codigo_nuevo_archivo.csv` | 96 | `f97651e636964b789208b1c29b37c10e19eec5c7fee80e23b07be6be3f28b348` |
| `comparacion_codigo_nuevo.csv` | 134 | `d2b664863abb6c370a1099599273e6842df9ebbe30e363e79f56773e9a98d356` |
| `issues.csv` | 55 | `600ddb52e9dc790a6c326064276538a9f805ab06c6544e7a668c459e01e491d2` |
| `medidas_archivo.csv` | 96 | `2c023fdf82c840979d6ff867391f20a8e23ee5c13e667ebff921cf6336418f53` |
| `medidas_proyecto.csv` | 1 | `5a0f30008504dd4244b36a3aaa793889b94730e70ce7e62bd7316240c98a568f` |
| `quality_gate.csv` | 4 | `80a9e0eac609a09f658adee373d8202367f7eb66b8fc49e8e1d31e5aa2c02500` |

## `corpus-jfreechart/`

| Fecha | Versión | Commit | Perfil | Tests | JaCoCo | Resultado |
|---|---|---|---|---|---|---|
| 2026-10-13T15:21:22 | 1.5.5 | `cb8ff67d983b` | Sonar way comprehensive | sí | sí | ok |
| 2026-10-13T15:35:02 | 1.5.6 | `703427c2acf0` | Sonar way comprehensive | sí | sí | ok (gate rechazado) |

| Archivo | Filas | SHA-256 |
|---|---|---|
| `codigo_nuevo_archivo.csv` | 694 | `9b3cc77dc022526704f2c87180c3f8af2e414a5333b524cd33a07bba55d4970d` |
| `comparacion_codigo_nuevo.csv` | 1016 | `72c9122937749acb2bba96877866dfa668edcff49d0fb0aacaa3f2332661faca` |
| `issues.csv` | 3117 | `ac03b424137d60da63bd41a922c75b1f111b2201eafe1e46f0691a086a7794f2` |
| `medidas_archivo.csv` | 694 | `d3f3bb9cfbd80f141e75cc279246a260ed563404a18568ccfdee63f09d2c3dc3` |
| `medidas_proyecto.csv` | 1 | `f97f1fd1303da7eae52ea97cf34e96fba0d0c952be22cacdaa34b5ed39b34c5d` |
| `quality_gate.csv` | 4 | `0b0b18e11d88f3b64fb7427acf19a4427043ee46d20771262255e157da0dc630` |

## `corpus-jsoup/`

| Fecha | Versión | Commit | Perfil | Tests | JaCoCo | Resultado |
|---|---|---|---|---|---|---|
| 2026-10-13T15:01:54 | 1.22.2 | `ac28afe6e5bf` | Sonar way comprehensive | sí | sí | ok |
| 2026-10-13T15:07:43 | 1.23.2 | `fbc7775c462f` | Sonar way comprehensive | sí | sí | ok (gate rechazado) |

| Archivo | Filas | SHA-256 |
|---|---|---|
| `codigo_nuevo_archivo.csv` | 96 | `679bf3a738c5b80340f5c2221d2f250e4d16753bdf8c12fa590f1b26301d0806` |
| `comparacion_codigo_nuevo.csv` | 134 | `30b0d9865421fb5b2863838d999a94a314d38c98312ff541fc238142972b4024` |
| `issues.csv` | 1003 | `5d21642e573da6d5cdcd7831e784cdd0c111dc184d4c72a2f0777d1a699bcaa4` |
| `medidas_archivo.csv` | 96 | `4f415ea654879ee3f222601a1c2c58b569b43a63b79a83c0982c67a168aa3bc3` |
| `medidas_proyecto.csv` | 1 | `d636499b2fe581140144d816ffc4a78d53ebe334a479c84972222c6047495753` |
| `quality_gate.csv` | 4 | `49e337ac3f1e0e43f1aaba755a722988168f10e6f5e276b5ceb804f880e6b728` |

## `diff-commons-collections/`

| Archivo | Filas | SHA-256 |
|---|---|---|
| `archivos.csv` | 677 | `0e0ae1653ab9d806b49afd5a6bcd3419d61642089d250c2b0fe7cefc3f6153a7` |

## `diff-commons-io/`

| Archivo | Filas | SHA-256 |
|---|---|---|
| `archivos.csv` | 271 | `85521529499729afc83d027f22f27b5a6c61be4d9b178ad0a6eeb7190f1584a9` |

## `diff-jfreechart/`

| Archivo | Filas | SHA-256 |
|---|---|---|
| `archivos.csv` | 1010 | `9f37ea80b140842b735dac7a7503357fd99f994daebe682c0c4f43011d853eeb` |

## `diff-jsoup/`

| Archivo | Filas | SHA-256 |
|---|---|---|
| `archivos.csv` | 84 | `025ead377a5d404f93f45986556729c7afb08f44ef217d853078ac9e7ac5a6fc` |

## `extraccion-commons-collections/`

| Fecha | Versión | Commit | Perfil | Tests | JaCoCo | Resultado |
|---|---|---|---|---|---|---|
| 2026-10-13T20:51:30 | 4.6.0 | `4107624de41a` | (administrado por complejidad_por_metodo.py) | no | no | ok |

| Archivo | Filas | SHA-256 |
|---|---|---|
| `complejidad_metodo.csv` | 4722 | `6e6bf5b3167d380f23662a480b71696e0fc7c01b11321a5421aa00460df4600f` |
| `eje2_metodos.csv` | 4720 | `1741c956c0d63d54c63402e21ae41bbf33afa559d49714bed85ffb5706a5dc38` |

## `extraccion-commons-io/`

| Fecha | Versión | Commit | Perfil | Tests | JaCoCo | Resultado |
|---|---|---|---|---|---|---|
| 2026-10-13T21:20:46 | 2.22.0 | `c14acc16f73e` | (administrado por complejidad_por_metodo.py) | no | no | ok |

| Archivo | Filas | SHA-256 |
|---|---|---|
| `complejidad_metodo.csv` | 3083 | `c839d9f0d59a10b5b8401ac6600e790c86bc400ad6d220728b43dc0bfd946ea6` |
| `eje2_metodos.csv` | 3081 | `e01820a7fdae4d563eb7866055010aeedfbf4d3eaebdf0f2442820b84916d7b7` |

## `extraccion-jfreechart/`

| Fecha | Versión | Commit | Perfil | Tests | JaCoCo | Resultado |
|---|---|---|---|---|---|---|
| 2026-10-13T20:01:23 | 1.5.6 | `703427c2acf0` | (administrado por complejidad_por_metodo.py) | no | no | ok |

| Archivo | Filas | SHA-256 |
|---|---|---|
| `complejidad_metodo.csv` | 7893 | `8deebe49bc52ad1232aece36677133aa27748bc15d11fb4825e89a61ce1d8a78` |
| `eje2_metodos.csv` | 7893 | `3d448b7b120864dc9b1a7af5419abce2aa93294554422787d7e6a0f998a30814` |

## `extraccion-jsoup/`

| Fecha | Versión | Commit | Perfil | Tests | JaCoCo | Resultado |
|---|---|---|---|---|---|---|
| 2026-10-12T23:57:51 | 1.23.2 | `fbc7775c462f` | TP extraccion complejidad | no | no | ok |
| 2026-10-13T19:36:07 | 1.23.2 | `fbc7775c462f` | (administrado por complejidad_por_metodo.py) | no | no | ok |

| Archivo | Filas | SHA-256 |
|---|---|---|
| `complejidad_metodo.csv` | 2088 | `47fc94ee28f2e6c8384354a666b253292ce5d631f42b6b9d8b781a3dd69df40a` |
| `eje2_metodos.csv` | 2088 | `84998178afbfb9cddfda8f90a0a29bc04518cf5d474ede73ed609fd05f741011` |

## `pmd-commons-collections-4.6.0/`

| Archivo | Filas | SHA-256 |
|---|---|---|
| `metodos.csv` | 5038 | `7ebe162ca4ff647943f0ce09a23df15f9ac44c0956ad24704743a13676d8da39` |

## `pmd-commons-io-2.22.0/`

| Archivo | Filas | SHA-256 |
|---|---|---|
| `metodos.csv` | 3184 | `457be2ef71bc3405ac1355296b59ccb1887ca110a7f89f29d21f2c57bbfd91d8` |

## `pmd-jfreechart-1.5.6/`

| Archivo | Filas | SHA-256 |
|---|---|---|
| `metodos.csv` | 9091 | `ab839129ab02582859887cf7df0174fe041e2c2401881c61b1fc093ab08de08c` |

## `pmd-jsoup-1.23.2/`

| Archivo | Filas | SHA-256 |
|---|---|---|
| `metodos.csv` | 2243 | `fef6c0f099df69800e7b2063f540ae5caae513f25044b0f6f0e4937a7558f1e2` |

## `propio-poo2025/`

| Fecha | Versión | Commit | Perfil | Tests | JaCoCo | Resultado |
|---|---|---|---|---|---|---|
| 2026-11-18T11:38:08 | 2026-03-13 | `cbccd2676cc7` | Sonar way comprehensive | no | no | ok |

| Archivo | Filas | SHA-256 |
|---|---|---|
| `issues.csv` | 60 | `d07fa7e61d459fd7a038338e6c485d5517d77d7fa5e3f67d90b61a83c4bdaa42` |
| `medidas_archivo.csv` | 91 | `1d73e5d63b3d8f114d3fd854daf6b0d9c9df3d02bf2bb43faa3ea88dc7fd5816` |
| `medidas_proyecto.csv` | 1 | `2f70855aad8ee0b6db3ad9bfc53c49e2dbde6148cbdd32913ed05b3cf9bf18e5` |
| `planilla-clasificacion.csv` | 60 | `149ba7d5aabdbf75139e66fc8ee6666c109bca0c60c9f5a614400f8b9e825c28` |
| `quality_gate.csv` | 1 | `5d88280f10a8cc152bba7f4fe8fe6805c79fe3af1e2b26943b273079abd9d47e` |

## `prueba-comp-jsoup/`

| Fecha | Versión | Commit | Perfil | Tests | JaCoCo | Resultado |
|---|---|---|---|---|---|---|
| 2026-10-13T13:52:11 | 1.23.2 | `fbc7775c462f` | Sonar way comprehensive | no | no | ok |

| Archivo | Filas | SHA-256 |
|---|---|---|
| `issues.csv` | 1003 | `5340d9f2798368db9438baeba16956203452a13f01fb9688fd7538a01f6bf16f` |
| `medidas_archivo.csv` | 96 | `1cb7d5eea5ff2ee56f408dda06bb544e9fbe9069d7f7ee20dbc21d44eefbe41d` |
| `medidas_proyecto.csv` | 1 | `bbb8da7538e49af7b1539cca1dfe563eff4f06a05b84a76ea5e6ba60198efe49` |
| `quality_gate.csv` | 1 | `5d88280f10a8cc152bba7f4fe8fe6805c79fe3af1e2b26943b273079abd9d47e` |
| `supuestos.md` | 21 | `e94618b291a82cfe516b7668077b500b664cc2e5104c592224b8971a768c3b35` |

## `prueba-pt1-jsoup/`

| Fecha | Versión | Commit | Perfil | Tests | JaCoCo | Resultado |
|---|---|---|---|---|---|---|
| 2026-10-12T20:30:08 | 1.23.2 | `fbc7775c462f` | Sonar way core | no | no | ok |

| Archivo | Filas | SHA-256 |
|---|---|---|
| `issues.csv` | 55 | `bd11a31815be2bf022648bec1dcfe40429061ae4232954b232373caf9eac9aec` |
| `medidas_archivo.csv` | 96 | `16e7edd6462935bb2ec8526a5167b0c1b64780167316f4f735ce957bd5409d3e` |
| `medidas_proyecto.csv` | 1 | `019b69ad13297cb09d88ecd58f1775ba2968928b909e5a476401c04275210815` |
| `quality_gate.csv` | 1 | `5d88280f10a8cc152bba7f4fe8fe6805c79fe3af1e2b26943b273079abd9d47e` |
| `supuestos.md` | 21 | `79134d0a3b7246f0749796a3a42aa1884bc6a176ea4869e395f5f348ce65d500` |

## `prueba-pt3-jsoup/`

| Fecha | Versión | Commit | Perfil | Tests | JaCoCo | Resultado |
|---|---|---|---|---|---|---|
| 2026-10-13T11:28:49 | 1.22.2 | `ac28afe6e5bf` | Sonar way core | no | no | ok |
| 2026-10-13T11:32:27 | 1.23.2 | `fbc7775c462f` | Sonar way core | no | no | ok (gate rechazado) |

| Archivo | Filas | SHA-256 |
|---|---|---|
| `codigo_nuevo_archivo.csv` | 96 | `b62b087fe98d2d97f7eb74d2226461c41777610d0b237ad4fa047deaf6025735` |
| `comparacion_codigo_nuevo.csv` | 134 | `d2b664863abb6c370a1099599273e6842df9ebbe30e363e79f56773e9a98d356` |
| `issues.csv` | 55 | `0ce9c3a0496486b125343d000f768397528b3bf61f788126fbea56f3615977db` |
| `medidas_archivo.csv` | 96 | `16e7edd6462935bb2ec8526a5167b0c1b64780167316f4f735ce957bd5409d3e` |
| `medidas_proyecto.csv` | 1 | `a9ae767d648538420ad94958c5555ac95b11d1334eb4679b03606b13f283e4c8` |
| `quality_gate.csv` | 4 | `ef92bf3dcbff7cc4453eab304efbe6eb257a8e177d6b774def2a4c111c8ca1cf` |

## `prueba-pt4-commons-io/`

| Fecha | Versión | Commit | Perfil | Tests | JaCoCo | Resultado |
|---|---|---|---|---|---|---|
| 2026-10-13T12:48:56 | 2.22.0 | `c14acc16f73e` | Sonar way core | sí | sí | ok |

| Archivo | Filas | SHA-256 |
|---|---|---|
| `issues.csv` | 96 | `cadcf454e208e8e7c5a3c191a9323cf2843af2895b3651771cbba89db24e5e8a` |
| `medidas_archivo.csv` | 277 | `2f0124eb9e0d852bd365e4831dbadaa6612133b2a31c69dc43727736d685539e` |
| `medidas_proyecto.csv` | 1 | `fc4a71a44c7e739aad8328d1a891adbe9683cab2a044ac95a3b68534fee617a8` |
| `quality_gate.csv` | 1 | `5d88280f10a8cc152bba7f4fe8fe6805c79fe3af1e2b26943b273079abd9d47e` |

## `prueba-pt4-jsoup/`

| Fecha | Versión | Commit | Perfil | Tests | JaCoCo | Resultado |
|---|---|---|---|---|---|---|
| 2026-10-13T12:09:08 | 1.22.2 | `ac28afe6e5bf` | Sonar way core | sí | sí | falla (código 1) |
| 2026-10-13T12:13:36 | 1.23.2 | `fbc7775c462f` | Sonar way core | sí | sí | falla (código 1) |
| 2026-10-13T12:24:27 | 1.22.2 | `ac28afe6e5bf` | Sonar way core | sí | sí | ok |
| 2026-10-13T12:31:33 | 1.23.2 | `fbc7775c462f` | Sonar way core | sí | sí | ok (gate rechazado) |

| Archivo | Filas | SHA-256 |
|---|---|---|
| `codigo_nuevo_archivo.csv` | 96 | `f97651e636964b789208b1c29b37c10e19eec5c7fee80e23b07be6be3f28b348` |
| `issues.csv` | 54 | `ac7e5997dfc171b2ecd9fb5a55a2e7c01475f4ada11bd05932065d27ccfa6ffc` |
| `medidas_archivo.csv` | 96 | `2c023fdf82c840979d6ff867391f20a8e23ee5c13e667ebff921cf6336418f53` |
| `medidas_proyecto.csv` | 1 | `e0ccdc56111aa3293eaf5dc252735b2e0f6c252ae4299614cb1fec515b0240eb` |
| `quality_gate.csv` | 4 | `80a9e0eac609a09f658adee373d8202367f7eb66b8fc49e8e1d31e5aa2c02500` |

## `prueba-pt4-jsoup-raices/`

| Fecha | Versión | Commit | Perfil | Tests | JaCoCo | Resultado |
|---|---|---|---|---|---|---|
| 2026-10-13T12:40:27 | 1.23.2 | `fbc7775c462f` | Sonar way core | sí | sí | ok |

| Archivo | Filas | SHA-256 |
|---|---|---|
| `issues.csv` | 55 | `bae0d16b63ffa11b632ced81c6dc004f2cd597827f9f5ad407d56005324c169f` |
| `medidas_archivo.csv` | 96 | `2c023fdf82c840979d6ff867391f20a8e23ee5c13e667ebff921cf6336418f53` |
| `medidas_proyecto.csv` | 1 | `8d38b90e3aa5d91d90a0a963cf82c360562a43ae58013cdcca6bbbb2894eb805` |
| `quality_gate.csv` | 1 | `5d88280f10a8cc152bba7f4fe8fe6805c79fe3af1e2b26943b273079abd9d47e` |

## `prueba-pt4-jsoup-v1/`

| Fecha | Versión | Commit | Perfil | Tests | JaCoCo | Resultado |
|---|---|---|---|---|---|---|
| 2026-10-13T11:52:30 | 1.23.2 | `fbc7775c462f` | Sonar way core | sí | sí | ok |

| Archivo | Filas | SHA-256 |
|---|---|---|
| `issues.csv` | 55 | `34193a306a461c7a132cbfcf2cb5e45ac72fe8199798aef48f0e0f383ac11cb6` |
| `medidas_archivo.csv` | 96 | `5a88a528e8f0ec4a8c2e35d05975369274cfbd0d518f3719fc188e8a9b2fca1c` |
| `medidas_proyecto.csv` | 1 | `df6e85f4c5d00036dd3a52e023991c719613490a6bab56a90f2a1705e9364190` |
| `quality_gate.csv` | 1 | `5d88280f10a8cc152bba7f4fe8fe6805c79fe3af1e2b26943b273079abd9d47e` |

## Archivos sueltos

| Archivo | Filas | SHA-256 |
|---|---|---|
| `.gitkeep` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `compilacion.csv` | 8 | `f37f1d697951b76ad8bce87228fbc53ae6c4b07faa190ac9ea455288f08956fe` |
| `registro_analisis.csv` | 33 | `1af84a09549ef78b99876a2b93f0100b148873030201f43f70219d75ccdc5959` |
