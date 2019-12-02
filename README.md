# Plugin completude de Malhas Viárias

Esse plugin é o resultado final apresentado na disciplina de Projeto de Soluções de Geoinformação do Programa de Pós Graduação em Ciências Geodésicas. O problema proposto foi desenvolver um sistema para um determinado grupo utilizando o método User centred design (UCD) que incorpora a perspectiva do usuário no desenvolvimento do sistema, de modo que haja uma boa usabilidade.

## Descrição do Sistema solicitado
Plugin QGIS para identificação da completude de malhas viárias por meio da comparação de dados de referência fornecidos pelo usuário com dados do Open Street Map (OSM).
### Usuários potênciais:
* Administração pública (tomadores de decisão da esfera municipal e/ou regional).
* Profissionais da área de planejamento urbano e infraestrutura.
* Estudantes, professores, pesquisadores, etc.
### Requisitos do sistema
1. A solução deverá, a partir da camada de estudo fornecida pelo usuário, definir um retângulo envolvente onde serão realizadas as análises espaciais.
2. A solução deverá reconhecer, por meio da camada de estudo fornecida pelo usuário, a região a ser analisada  e, em seguida, carregar os dados da camada de validação.
3. A solução deverá, por meio da definição da escala de análise (resolução da grade) por parte do usuário, desenhar uma grade regular para a delimitar as análises espaciais.
4. A solução deverá analisar cada um dos quadrantes definidos na grade utilizando as camadas de estudo e de validação.
5. Calcular a diferença em comprimento em cada quadrante entre a base oficial e OSM
6. A solução deverá classificar o grau de correspondência das camadas analisadas por quadrante.

## Produto Final
A solução proposta foi um plugin no software QGIS, que tem como camada de entrada dados vetorias lineares referente a malha viária escolhidas pelo usuário. Assim, é feita uma comparação entre a camada de entrada e a base do Open Street Map, gerando uma grade regular que possibilita a categorização da diferença métrica entre as duas camadas vetoriais.
### Projeto gráfico da interface
![Interface1](https://user-images.githubusercontent.com/36965321/69979959-2eb8eb00-1527-11ea-9c21-3233eaafce5b.png)
![Interface2](https://user-images.githubusercontent.com/36965321/69979965-34163580-1527-11ea-9a6f-6bd8ed530079.png)
#### Dados de entrada
* Camada de referência: malha viária a ser analisada;
* Extensão da área de estudo;
* Resolução da grade (em metros)
#### Dados de saída
Grade vetorial derivada da diferença métrica e normalizada na escala de 1 a -1
* 1 = Malha de referência em maior quantidade comparado ao OSM
* 0 = Mesma quantidade métrica entre a camada de referência e o OSM
* -1 = OSM em maior quantidade comparado a camada de referência
#### Dependência
Plugin Quick OSM
### Infograficos do Sistema
Os infograficos a seguir apresentam quais são as ações do usuário na utilização do plugin, bem como quais processos o plugin realiza para o desenvolvimento do resultado final desejado, respectivamente.

![Info_Usuario](https://user-images.githubusercontent.com/36965321/69980284-d20a0000-1527-11ea-8512-251b3ac0bb20.png)
![Info_Plugin](https://user-images.githubusercontent.com/36965321/69980312-df26ef00-1527-11ea-89a6-c942bd527c97.png)

### Projeto Cartográfico do dado de saída
![proj_cart](https://user-images.githubusercontent.com/36965321/69981767-e0a5e680-152a-11ea-82ee-bc9b2adc9c56.PNG)

### Exemplos dos resultados obtidos com o plugin
* Camada de entrada = Malha viária de Curitiba
1. Resolução da grade = 1000 metros
![Projetos_Resultado](https://user-images.githubusercontent.com/36965321/69979569-73905200-1526-11ea-90df-6f2cd9913b8b.png)

2. Resolução da grade = 200 metros
![Projetos_Resultado_200m](https://user-images.githubusercontent.com/36965321/69979669-9f133c80-1526-11ea-9499-26da4311d675.png)
