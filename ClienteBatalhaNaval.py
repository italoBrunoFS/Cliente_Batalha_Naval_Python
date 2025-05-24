#GRUPO:

# Italo Bruno da Fonseca Souto
# Alexandre Lucas Justino Guedes

import socket
import sys

class ClienteBatalhaNaval:
    PORTA_SERVIDOR = 50000
    ENDERECO_IP = "56.124.35.55"
    TAMANHO_BUFFER = 512

    def __init__(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.settimeout(10)  # Timeout de 10 segundos para caso servidor não responda
        self.destino = (self.ENDERECO_IP, self.PORTA_SERVIDOR)
        self.senha = ""
        self.n_sessao = 0

    #Função que lida com o envio de requisições e recebe as respostas do servidor, caso haja timeout ou alguma outra exceção retorna "none", se não, retorna a resposta
    def enviar_requisicao(self, mensagem: bytearray):
        try:
            self.socket.sendto(mensagem, self.destino)
            resposta, _ = self.socket.recvfrom(self.TAMANHO_BUFFER)
            return resposta
        except socket.timeout:
            print("Erro: tempo de resposta esgotado (timeout).\n")
            return None
        except socket.error as e:
            print(f"Erro de socket: {e}")
            return None
    
    # Função para criar sessão no servidor, cria e envia a mensagem de criar sessão e depois guarda a resposta do servidor, caso a resposta seja válida e o status indique sucesso,
    # atribui-se o número da sessão e retorna true, caso contrário, retorna false 
    def criar_sessao(self):
        tipo = 0
        tamanho_senha = len(self.senha)
        cabecalho = (tipo << 5) | tamanho_senha # 3 bits do tipo + 5 bits do tamanho da senha

        senha_bytes = self.senha.encode("utf-8")
        mensagem = bytearray() # cria mensagem
        mensagem.append(cabecalho)
        mensagem.extend(senha_bytes)

        resposta = self.enviar_requisicao(mensagem)
        if resposta is None:
            return False

        if resposta[0] >> 5 == 4:
            status = resposta[0] & 0b11111 # 5 bits menos significativos
            if status == 0:
                self.n_sessao = resposta[1] # N_sessão definido
                return True
            else:
                print("Erro ao criar sessão")
                return False
        else:
            print("Resposta inesperada!")
            return False
    
    # Função que envia a jogada de 3 bytes ao servidor e recebe sua resposta, caso a resposta seja válida e o status = 0 (sucesso) imprime o conteúdo do campo info da resposta,
    # caso contrário imprime uma mensagem de erro
    def realizar_jogada(self, jogada: str):
        tipo = 1
        tamanho_senha = len(self.senha)
        cabecalho = (tipo << 5) | tamanho_senha
        
        # Cria uma array de 3 bytes para a jogada e converte a string, se a jogada tiver 2 bytes, o terceiro byte será 0 (\0 para string) como solicitado.
        jogada_bytes = bytearray(3)
        jogada_bytes[0:len(jogada[:3])] = jogada[:3].encode("utf-8")

        senha_bytes = self.senha.encode("utf-8")
        mensagem = bytearray() # cria mensagem
        mensagem.append(cabecalho)
        mensagem.append(self.n_sessao)
        mensagem.extend(jogada_bytes)
        mensagem.extend(senha_bytes)

        resposta = self.enviar_requisicao(mensagem) # guarda resposta
        if resposta is None:
            return

        if resposta[0] >> 5 == 4:
            status = resposta[0] & 0b11111
            tamanho_info = (resposta[3] << 8) | resposta[2] # Foi necessário realizar essa inversão dos bytes, pois na ordem direta o tamanho_info estava vindo irrealisticamente grande.

            if len(resposta) >= 4 + tamanho_info:
                info = resposta[4:4 + tamanho_info].decode("utf-8") # guarda info (Vai do quarto byte até 4 + tamanho_info)
                if status == 0:
                    print(info)
                else:
                    print(f"Erro ao realizar jogada! Detalhe: {info}")
            else:
                print("Erro: resposta recebida está incompleta ou corrompida.")
        else:
            print("Resposta inesperada!")
    
    # Função para a trapaça, tal qual a função de realizar jogada monta a mensagem e guarda a resposta do servidor, caso seja válida imprime o campo info da resposta (A trapaça),
    # caso contrário, imprime uma mensagem de erro
    def hackear(self):
        tipo = 2
        tamanho_senha = len(self.senha)
        cabecalho = (tipo << 5) | tamanho_senha # 3 bits tipo + 5 bits tamanho senha

        senha_bytes = self.senha.encode("utf-8")
        mensagem = bytearray() # monta mensagem
        mensagem.append(cabecalho)
        mensagem.append(self.n_sessao)
        mensagem.extend(senha_bytes)

        resposta = self.enviar_requisicao(mensagem) # guarda resposta
        if resposta is None:
            return

        if resposta[0] >> 5 == 4:
            status = resposta[0] & 0b11111
            tamanho_info = (resposta[3] << 8) | resposta[2] # novamente foi necessário inverter a ordem dos bytes para funcionar

            if len(resposta) >= 4 + tamanho_info: # A mensagem precisa ter pelo menos 4 bytes: cabeçalho + N_sessão + tamanho_info
                info = resposta[4:4 + tamanho_info].decode("utf-8")
                if status == 0:
                    print(info)
                else:
                    print(f"Erro ao Hackear! Detalhe: {info}")
            else:
                print("Resposta corrompida!")
        else:
            print("Resposta inesperada!")

    # Função para encerrar sessão, envia uma mensagem de encerrar sessão para o servidor e guarda a resposta, se a resposta for válida, imprime uma confirmação, caso contrário
    # imprime uma mensagem de erro + o campo info do server.
    # Obs: Por se tratar um cliente UDP e não ter muito o que fazer para tratar dos erros do lado do cliente, cogitamos em não colocar depuração de erro, mas decidimos manter
    # por questões de boa prática!
    def encerrar_sessao(self):
        tipo = 3
        tamanho_senha = len(self.senha)
        cabecalho = (tipo << 5) | tamanho_senha

        senha_bytes = self.senha.encode("utf-8")
        mensagem = bytearray()
        mensagem.append(cabecalho)
        mensagem.append(self.n_sessao)
        mensagem.extend(senha_bytes)

        resposta = self.enviar_requisicao(mensagem)
        if resposta is None:
            return

        if resposta[0] >> 5 == 4:
            status = resposta[0] & 0b11111
            if status == 0:
                print("SESSÃO ENCERRADA!")
            else:
                print("Erro ao Encerrar Sessão")
                tamanho_info = (resposta[3] << 8) | resposta[2]
                if len(resposta) >= 4 + tamanho_info:
                    info = resposta[4:4 + tamanho_info].decode("utf-8")
                    print(f"Detalhe: {info}")
        else:
            print("Resposta inesperada!")



if __name__ == "__main__":
    cliente = ClienteBatalhaNaval()
    
    # loops dos menus, quando o usúario inicia uma sessão é solicitada a criação de uma senha e enviada a requisição de criar sessão pelo cliente, se a função retornar true, o usúario
    # entra no menu secundário. Para voltar ao menu principal é necessário encerrar a sessão.
    while True:
        print("=== MENU PRINCIPAL ===")
        print("1 - Iniciar sessao de jogo")
        print("2 - Sair")

        op1 = input("Digite uma opcao: ")
        if op1 == "1":
            cliente.senha = input("Digite a senha da sessao (max. 31 caracteres): ") # salva senha

            if cliente.criar_sessao():

                while True:
                    print(f"\nCONECTADO NA SALA {cliente.n_sessao}\n")
                    print("1 - Realizar Jogada")
                    print("2 - Hackear")
                    print("3 - Encerrar Sessao\n")
                    op2 = input("Digite sua opcao: ")

                    if op2 == "1":
                        jogada = input("Digite sua jogada (ex: A5): ")
                        cliente.realizar_jogada(jogada)
                    elif op2 == "2":
                        cliente.hackear()
                    elif op2 == "3":
                        print("GG")
                        cliente.encerrar_sessao()
                        break
        elif op1 == "2":
            break