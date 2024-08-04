#include <stdio.h>
#include <string.h>
#include <time.h>
#include <stdlib.h>
#include <misc/util/abc_global.h>
#include <misc/extra/extra.h>
#include <base/abc/abc.h>
#include <base/io/ioReadBench.c>
#include <base/io/io.c>
#include <base/main/main.h>
#include <misc/extra/extraUtilReader.c>
#include <misc/vec/vec.h>
#include <base/io/ioWriteBench.c>

Extra_FileReader_t *Extra_FileReaderAllocFromString(char *pFileContent, char *pCharsComment, char *pCharsStop, char *pCharsClean)
{
    Extra_FileReader_t *p;
    char *pChar;
    int nCharsToRead;

    // start the file reader
    p = ABC_ALLOC(Extra_FileReader_t, 1);
    memset(p, 0, sizeof(Extra_FileReader_t));
    p->pFileName = "filename.bench"; // No file name since content is provided directly
    p->pFile = NULL; // No file pointer since content is provided directly

    // set the character map
    memset(p->pCharMap, EXTRA_CHAR_NORMAL, 256);
    for (pChar = pCharsComment; *pChar; pChar++)
        p->pCharMap[(unsigned char)*pChar] = EXTRA_CHAR_COMMENT;
    for (pChar = pCharsStop; *pChar; pChar++)
        p->pCharMap[(unsigned char)*pChar] = EXTRA_CHAR_STOP;
    for (pChar = pCharsClean; *pChar; pChar++)
        p->pCharMap[(unsigned char)*pChar] = EXTRA_CHAR_CLEAN;

    // get the content size, in bytes
    p->nFileSize = strlen(pFileContent);

    // allocate the buffer
    p->pBuffer = ABC_ALLOC(char, EXTRA_BUFFER_SIZE + 1);
    p->nBufferSize = EXTRA_BUFFER_SIZE;
    p->pBufferCur = p->pBuffer;

    // determine how many chars to read
    nCharsToRead = EXTRA_MINIMUM(p->nFileSize, EXTRA_BUFFER_SIZE);

    // load the first part into the buffer
    strncpy(p->pBuffer, pFileContent, nCharsToRead);
    p->nFileRead = nCharsToRead;

    // set the pointers to the end and the stopping point
    p->pBufferEnd = p->pBuffer + nCharsToRead;
    p->pBufferStop = (p->nFileRead == p->nFileSize) ? p->pBufferEnd : p->pBuffer + EXTRA_BUFFER_SIZE - EXTRA_OFFSET_SIZE;

    // start the arrays
    p->vTokens = Vec_PtrAlloc(100);
    p->vLines = Vec_IntAlloc(100);
    p->nLineCounter = 1; // 1-based line counting

    return p;
}

char* runAbcCommands(char *pFileContent, const char *sCommand)
{
    Abc_Frame_t *pAbc = Abc_FrameGetGlobalFrame();

    // start the file
    Extra_FileReader_t *p = Extra_FileReaderAllocFromString(pFileContent, "#", "\n\r", " \t,()=");

    // read the network
    Abc_Ntk_t *pNtk = Io_ReadBenchNetwork(p);
    pNtk = Abc_NtkToLogic(pNtk);

    Abc_FrameReplaceCurrentNetwork(pAbc, pNtk);
    Abc_FrameCopyLTLDataBase(pAbc, pNtk);
    Abc_FrameClearVerifStatus(pAbc);

    Cmd_CommandExecute(pAbc, sCommand);

    Abc_Ntk_t *pNtkTemp = Abc_NtkToNetlistBench(pNtk);

    char *buffer;
    size_t size;
    FILE *memFile = open_memstream(&buffer, &size);
    Io_WriteBenchOne(memFile, pNtkTemp);
    fclose(memFile);

    return buffer;
}

int main(int argc, char *argv[])
{
    char *pFileContent = "INPUT(0)\nINPUT(1)\n2 = AND(0, 1)\n3 = NOT(0)\n4 = AND(3, 0)\n5 = AND(2, 4)\nOUTPUT(5)";
    const char *sCommand = "strash; dc2; dc2; dc2";

    char *buffer = runAbcCommands(pFileContent, sCommand);

    printf("%s", buffer);
    free(buffer);

    return 0;
}
