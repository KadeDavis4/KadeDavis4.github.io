#include <stdio.h>
#include <stdbool.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/wait.h> 
#include <fcntl.h>
#include <signal.h>
#define INPUT_LENGTH 2048
#define MAX_ARGS 512


int mode = 0;
int status = 0;

struct command_line
    {
        char *argv[MAX_ARGS + 1];
        int argc;
        char *input_file;
        char *output_file;
        bool is_bg;
    };
struct command_line *parse_input()
{
    char input[INPUT_LENGTH];
    struct command_line *curr_command = (struct command_line *) calloc(1,
    sizeof(struct command_line));
    // Get input
    printf(": ");
    fflush(stdout);
    fgets(input, INPUT_LENGTH, stdin);
    // Tokenize the input
    char *token = strtok(input, " \n");
    while(token){
    if(!strcmp(token,"<")){
    curr_command->input_file = strdup(strtok(NULL," \n"));
} else if(!strcmp(token,">")){
    curr_command->output_file = strdup(strtok(NULL," \n"));
} else if(!strcmp(token,"&")){
    curr_command->is_bg = true;
} else{
    curr_command->argv[curr_command->argc++] = strdup(token);
}
    token=strtok(NULL," \n");
}
    return curr_command;
}

void exit_input(){
    exit(0);
}

void status_input(){
    if (WIFEXITED(status)){
        printf("exit value %d\n", WEXITSTATUS(status));
        fflush(stdout);
    }else{
        printf("terminated by signal %d\n", WTERMSIG(status));
        fflush(stdout);
    }
}

void cd_input(char *filepath){
    if (chdir(filepath) != 0){
        perror("chir failed");
    }
}

void handle_SIGTSTP(int signo){
    
    if (mode == 0){
        mode = 1;
        char *message = "Entering foreground-only mode (& is now ignored)\n";
        write(STDOUT_FILENO, message, strlen(message));
    }else{
        mode = 0;
        char *message = "Exiting foreground-only mode\n";
        write(STDOUT_FILENO, message, strlen(message));
    }
}










int main()
{
    struct command_line *curr_command;
    char *inputpath = NULL;
    int childStatus;
    int childPid;

    pid_t bgPIDs[500];
    int BGs = 0;

    struct sigaction SIGINT_action = {0};
    SIGINT_action.sa_handler = SIG_IGN;
    sigfillset(&SIGINT_action.sa_mask);
    SIGINT_action.sa_flags = 0;
    sigaction(SIGINT, &SIGINT_action, NULL);

    struct sigaction SIGTSTP_action = {0};
    SIGTSTP_action.sa_handler = handle_SIGTSTP;
    sigfillset(&SIGTSTP_action.sa_mask);
    SIGTSTP_action.sa_flags = 0;
    sigaction(SIGTSTP, &SIGTSTP_action, NULL);



    while(true)
{
    sigaction(SIGINT, &SIGINT_action, NULL);
    SIGINT_action.sa_handler = SIG_IGN;

    for (int i = 0; i < BGs; i++){
        int pidStatus;
        int completed = waitpid(bgPIDs[i], &pidStatus, WNOHANG);
        if (completed > 0){
            if (WIFEXITED(pidStatus)){
                printf("background pid %d is done: exit value %d\n", bgPIDs[i], WEXITSTATUS(pidStatus));
                fflush(stdout);
            }else if (WIFSIGNALED(pidStatus)){
                printf("background pid %d is done: terminated by signal %d\n", bgPIDs[i], WTERMSIG(pidStatus));
                fflush(stdout);
            }
            bgPIDs[i] = bgPIDs[BGs - 1];
            BGs--;
            i--;
        }
    }




    curr_command = parse_input();
    if (curr_command->argc < 1){
        continue;
    }
    if (curr_command->argv[0][0] == '#'){
        continue;
    }

    if (mode == 1){
        curr_command->is_bg = false;
    }
    
    
    if (strcmp(curr_command->argv[0], "cd") == 0){
        
        if (curr_command->argc == 1){
            inputpath = getenv("HOME");
        }
        else{
            inputpath = curr_command->argv[1];
        }
        cd_input(inputpath);
        continue;
    }
    if (strcmp(curr_command->argv[0], "exit") == 0){
        exit_input();
        continue;
    }
    if (strcmp(curr_command->argv[0], "status") == 0){
        
        status_input();
        continue;
    }

    else{
        pid_t spawnpid = fork();
        switch(spawnpid){
            case -1:
                perror("fork() failed!");
                exit(1);
                break;
            case 0:
                // spawnpid is 0 in the child
                if (curr_command->is_bg){
                    SIGINT_action.sa_handler = SIG_IGN;
                }else{
                    SIGINT_action.sa_handler = SIG_DFL;
                }
                sigaction(SIGINT, &SIGINT_action, NULL);

                SIGTSTP_action.sa_handler = SIG_IGN;
                sigaction(SIGTSTP, &SIGTSTP_action, NULL);

                if (curr_command->input_file != NULL){
                    int sourceFD = open(curr_command->input_file, O_RDONLY);
                    if (sourceFD == -1){
                        printf("cannot open %s for input\n", curr_command->input_file);
                        fflush(stdout);
                        exit(1);
                    }
                    int result = dup2(sourceFD, 0);
                } 

                if (curr_command->output_file != NULL){
                    int targetFD = open(curr_command->output_file, O_WRONLY | O_CREAT | O_TRUNC, 0644);
                    if (targetFD == -1){
                        printf("cannot open %s for output\n", curr_command->output_file);
                        fflush(stdout);
                        exit(1);
                    }
                    int result = dup2(targetFD, 1);
                }

                if (curr_command->is_bg){
                    if (curr_command->input_file == NULL){
                        int devInRedir = open("/dev/null", O_RDONLY);
                        dup2(devInRedir, 0);
                    }
                    if (curr_command->output_file == NULL){
                        int devOutRedir = open("/dev/null", O_WRONLY | O_CREAT | O_TRUNC, 0644);
                        dup2(devOutRedir, 1);
                }}


                execvp(curr_command->argv[0], curr_command->argv);
                
                perror("File not found");
                exit(1);
                break;
            default:
                //parent
                if (curr_command->is_bg){
                    BGs++;
                    bgPIDs[BGs - 1] = spawnpid;
                    printf("background pid is %d\n", spawnpid);
                    fflush(stdout);
                }else{
                childPid = waitpid(spawnpid, &childStatus, 0);
                status = childStatus;
                }
                if (WIFSIGNALED(childStatus)) {
                    int signalNum = WTERMSIG(childStatus);
                    printf("terminated by signal %d\n", signalNum);
                    fflush(stdout);
    }
                break;
        }
    }
}



    return EXIT_SUCCESS;
}
